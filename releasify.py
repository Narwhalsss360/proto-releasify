from os import remove, chdir, getcwd, mkdir
from os.path import isfile, isdir, exists, basename
from shutil import Error as SHError, copy, move, copytree, rmtree
from sys import argv
from traceback import format_exc, print_exc
from yaml import load, CLoader, YAMLError

REMOVE_SELF_KEY = 'remove-self'
MANUAL_RESOLVE_KEY = 'manual-resolve'
ACTIONS_KEY = 'actions'
ACTION_KEY = 'action'
SRC_KEYS = ['src', 'path']
DST_KEY = 'dst'

def move_action(src: str, dst: str) -> None:
    '''move'''
    move(src, dst, copy if isfile(src) else copytree)

def copy_action(src: str, dst: str) -> None:
    (copy if isfile(src) else copytree)(src, dst)

def delete_action(path: str, _) -> None:
    (remove if isfile(path) else rmtree)(path)

def mkdir_action(path: str, _) -> None:
    mkdir(path)

def touch_action(name: str, _) -> None:
    with open(name, 'w') as _:
        ...

action_mappings = {
    'move': move_action,
    'copy': copy_action,
    'delete': delete_action,
    'mkdir': mkdir_action,
    'touch': touch_action
}

def get_or_default(kvps, obj, key, default):
    '''Get a value from a dictionary, if it does not exist, set to a defualt value'''

    if key in kvps:
        obj = kvps[key]
    else:
        print(f'Warning! {key} was not specified, defaulting to {default}.')
        obj = default
    return obj

def main():
    '''Main function'''
    global remove_self
    global manual_resolve

    configuration_file_name = 'releasify.yaml'
    if len(argv) > 1:
        configuration_file_name = argv[1]
    print(f'Using {configuration_file_name=}')

    if not exists(configuration_file_name):
        print(f'file {configuration_file_name=} does not exist')
        return

    file_folder = configuration_file_name.replace(basename(configuration_file_name), '')
    if file_folder != '':
        chdir(file_folder)
    with open(basename(configuration_file_name), 'r') as yaml_file:
        try:
            releasify_cfg = load(yaml_file, Loader=CLoader)
        except YAMLError:
            print('There was a releasify yaml file parse error.')
            print_exc()
            return

    chdir(get_or_default(releasify_cfg, '', 'working-directory', '.'))
    print(f'Working in {getcwd()}')

    remove_self = get_or_default(releasify_cfg, False, REMOVE_SELF_KEY, False)
    manual_resolve = get_or_default(releasify_cfg, True, MANUAL_RESOLVE_KEY, True)
    if ACTIONS_KEY in releasify_cfg:
        for action in releasify_cfg[ACTIONS_KEY]:
            if ACTION_KEY not in action:
                print(f'No action path specified for {action}.')
                continue

            if action[ACTION_KEY] not in action_mappings:
                print(f'Action specified does not exist: {action}.')
                continue

            src_key = list(filter(lambda x: x in action, SRC_KEYS))
            if len(src_key) == 0:
                print(f'No source path specified for {action}.')
                continue
            src_key = src_key[0]

            def exec():
                '''Wrapper to recursively retry'''
                try:
                    action_mappings[action[ACTION_KEY]](action[src_key], action[DST_KEY] if DST_KEY in action else None)
                except OSError:
                    print(f'There was an error executing {action=}.\n{format_exc()}{'Use "retry", or "skip"' if manual_resolve else ''}')
                    if not manual_resolve:
                        return
                    entry = input()
                    if entry.lower() == 'retry':
                        exec()

            exec()

    if remove_self:
        pass
        remove(__file__)

if __name__ == '__main__':
    main()
