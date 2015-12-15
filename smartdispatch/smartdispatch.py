from __future__ import absolute_import

import os
import re
import itertools
import time as t

import smartdispatch
from smartdispatch import utils
from smartdispatch.argument_template import argument_templates

UID_TAG = "{UID}"


def generate_name_from_command(command, max_length_arg=None, max_length=None):
    ''' Generates name from a given command.

    Generate a name by replacing spaces in command with dashes and
    by trimming lengthty (as defined by max_length_arg) arguments.

    Parameters
    ----------
    command : str
        command from which to generate the name
    max_length_arg : int
        arguments longer than this will be trimmed keeping last characters (Default: inf)
    max_length : int
        trim name if longer than this keeping last characters (Default: inf)

    Returns
    -------
    name : str
        slugified name
    '''
    if max_length_arg is not None:
        max_length_arg = min(-max_length_arg, max_length_arg)

    name = t.strftime("%Y-%m-%d_%H-%M-%S_")
    name += '_'.join([utils.slugify(argvalue)[max_length_arg:] for argvalue in command.split()])
    return name[:max_length]


def get_commands_from_file(fileobj):
    ''' Reads commands from `fileobj`.

    Parameters
    ----------
    fileobj : file
        opened file where to read commands from

    Returns
    -------
    commands : list of str
        commands read from the file
    '''
    return fileobj.read().strip().split('\n')


def unfold_command(command):
    ''' Unfolds a command into a list of unfolded commands.

    Unfolding is performed for every folded arguments (see *Arguments templates*)
    found in `command`. Then, resulting commands are generated using the product
    of every unfolded arguments.

    Parameters
    ----------
    command : list of str
        command to unfold

    Returns
    -------
    commands : list of str
        commands obtained after unfolding `command`

    Arguments template
    ------------------
    *list*: "[item1 item2 ... itemN]"
    *range*: "[start:end]" or "[start:end:step]"
    '''
    text = utils.encode_escaped_characters(command)

    # Build the master regex with all argument's regex
    regex = "(" + "|".join(["(?P<{0}>{1})".format(name, arg.regex) for name, arg in argument_templates.items()]) + ")"

    pos = 0
    arguments = []
    for match in re.finditer(regex, text):
        # Add already unfolded argument
        arguments.append([text[pos:match.start()]])

        # Unfold argument
        argument_template_name, matched_text = next((k, v) for k, v in match.groupdict().items() if v is not None)
        arguments.append(argument_templates[argument_template_name].unfold(matched_text))
        pos = match.end()

    arguments.append([text[pos:]])  # Add remaining unfolded arguments
    arguments = [list(map(utils.decode_escaped_characters, argvalues)) for argvalues in arguments]
    return ["".join(argvalues) for argvalues in itertools.product(*arguments)]


def replace_uid_tag(commands):
    return [command.replace("{UID}", utils.generate_uid_from_string(command)) for command in commands]


def get_available_queues(cluster_name=utils.detect_cluster()):
    """ Fetches all available queues on the current cluster """
    if cluster_name is None:
        return {}

    smartdispatch_dir, _ = os.path.split(smartdispatch.__file__)
    config_dir = os.path.join(smartdispatch_dir, 'config')

    config_filename = cluster_name + ".json"
    config_filepath = os.path.join(config_dir, config_filename)

    if not os.path.isfile(config_filepath):
        return {}  # Unknown cluster

    queues_infos = utils.load_dict_from_json_file(config_filepath)
    return queues_infos
