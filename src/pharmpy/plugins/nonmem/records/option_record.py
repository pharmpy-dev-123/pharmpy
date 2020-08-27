"""
Generic NONMEM option record class.

Assumes 'KEY=VALUE' and does not support 'KEY VALUE'.
"""

from collections import OrderedDict, namedtuple

from pharmpy.parse_utils.generic import AttrTree

from .record import Record


def _get_key(node):
    if hasattr(node, 'KEY'):
        return node.KEY
    else:
        return node.VALUE


def _get_value(node):
    if hasattr(node, 'KEY'):
        return node.VALUE
    else:
        return None


class OptionRecord(Record):
    @property
    def option_pairs(self):
        """ Extract the key-value pairs
            If no value exists set it to None
            Can only handle cases where options are supposed to be unique
        """
        pairs = OrderedDict()
        for node in self.root.all('option'):
            pairs[_get_key(node)] = _get_value(node)
        return pairs

    @property
    def all_options(self):
        """ Extract all options even if non-unique.
            returns a list of named two-tuples with key and value
        """
        Option = namedtuple('Option', ['key', 'value'])
        pairs = []
        for node in self.root.all('option'):
            pairs += [Option(_get_key(node), _get_value(node))]
        return pairs

    def has_option(self, name):
        return name in self.option_pairs.keys()

    def get_option_startswith(self, s):
        for opt in self.option_pairs.keys():
            if opt.startswith(s):
                return opt
        return None

    def set_option(self, key, new_value):
        """ Set the value of an option

            If option already exists replaces its value
            appends option at the end if it does not exist
            does not handle abbreviations yet
        """
        # If already exists update value
        last_option = None
        for node in self.root.all('option'):
            old_key = node.find('KEY')
            if str(old_key) == key:
                node.VALUE = new_value
                return
            last_option = node

        ws_node = AttrTree.create('ws', [{'WS_ALL': ' '}])
        option_node = self._create_option(key, new_value)
        # If no other options add first else add just after last option
        if last_option is None:
            self.root.children = [ws_node, option_node] + self.root.children
        else:
            new_children = []
            for node in self.root.children:
                new_children.append(node)
                if node is last_option:
                    new_children += [ws_node, option_node]
            self.root.children = new_children

    def _create_option(self, key, value=None):
        if value is None:
            node = AttrTree.create('option', [{'VALUE': key}])
        else:
            node = AttrTree.create('option', [{'KEY': key}, {'EQUAL': '='}, {'VALUE': value}])
        return node

    def append_option(self, key, value=None):
        """ Append option as last option

            Method applicable to option records with no special grammar
        """
        node = self._create_option(key, value)
        self.append_option_node(node)

    def append_option_node(self, node):
        """ Add a new option as last option
        """
        last_child = self.root.children[-1]
        if last_child.rule == 'option':
            ws_node = AttrTree.create('ws', [{'WS_ALL': ' '}])
            self.root.children += [ws_node, node]
        elif last_child.rule == 'ws':
            if '\n' in str(last_child):
                ws_node = AttrTree.create('ws', [{'WS_ALL': ' '}])
                self.root.children[-1:0] = [ws_node, node]
            else:
                self.root.children.append(node)
        else:
            ws_node = AttrTree.create('ws', [{'WS_ALL': '\n'}])
            self.root.children += [ws_node, node]

    def remove_option(self, key):
        """ Remove all options key
        """
        new_children = []
        for node in self.root.children:
            if node.rule == 'option':
                if key == _get_key(node):
                    if new_children[-1].rule == 'ws' and '\n' not in str(new_children[-1]):
                        new_children.pop()
                else:
                    new_children.append(node)
            else:
                new_children.append(node)
        self.root.children = new_children

    def remove_option_startswith(self, start):
        """ Remove all options that startswith
        """
        for key in self.option_pairs.keys():
            if key.startswith(start):
                self.remove_option(key)
