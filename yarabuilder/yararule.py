"""
Python representation of a YARA rule
"""

import collections
import logging


class YaraCommentEnabledClass:
    """
    Class to be inherited that contains comment utility functions
    """

    def __init__(self):
        """
        Constructor for the class
        (will be overridden by subclasses)
        """
        self.yara_comment = YaraComment()

    def add_comment(self, comment, position="inline"):
        """
        Add a comment entry

        Args:
            comment (str): the comment
            position (str): the position of the comment relative to the entry
        """
        if position == "above":
            self.yara_comment.above = comment

        elif position == "inline":
            self.yara_comment.inline = comment

        elif position == "below":
            self.yara_comment.below = comment

    def build_comments(self, raw, whitespace="    "):
        """
        Build the comment around the (built) entry its associated with

        Args:
            raw (str): the raw entry that has already been built (e.g. raw_meta_entry)
            whitespace (str): whitespace to use when building the comment

        Returns:
            str: the entry with comments built around it
        """
        if self.yara_comment.above:
            raw = "// %s\n%s%s%s" % (
                self.yara_comment.above,
                whitespace,
                whitespace,
                raw,
            )

        if self.yara_comment.inline:
            raw = "%s // %s" % (raw, self.yara_comment.inline)

        if self.yara_comment.below:
            raw = "%s\n%s%s// %s" % (
                raw,
                whitespace,
                whitespace,
                self.yara_comment.below,
            )

        return raw


class YaraComment:
    """
    Class to represent a comment (or multiple comments) in a YaraRule
    Can be applied to YaraMetaEntry and YaraString

    Attributes:
        above (str): comment located a line above the entry
        inline (str): comment located on the same line after the entry
        below (str): comment located a line below the entry
    """

    def __init__(self):
        """
        Constructor for YaraComment
        """
        self.above = None
        self.inline = None
        self.below = None


class YaraMetaEntry(YaraCommentEnabledClass):
    """
    Class to represent an entry in the meta section

    Attributes:
        yara_comment (YaraComment): the comment associated with this entry
        raw_meta_entry (str): variable to store the built meta_entry
    """

    def __init__(self, name, value, position, meta_type="text"):
        """
        Constructor for YaraMetaEntry

        Args:
            name (str): the name of the meta entry
            value (str, int, bool): the meta entry
            position (int): the position in the meta section
            meta_type (str): the type of the meta entry
        """
        self.name = name
        self.value = value
        self.position = position
        self.meta_type = meta_type
        self.yara_comment = YaraComment()
        self.raw_meta_entry = None

    def build_meta_entry(self, whitespace="    "):
        """
        Build a meta_entry into a string (stored in raw_meta_entry)

        Args:
            whitespace (str): whitespace to use when building the meta_entry
        """
        if self.meta_type == "text":
            self.raw_meta_entry = '%s = "%s"' % (self.name, self.value)

        elif self.meta_type == "int":
            self.raw_meta_entry = "%s = %d" % (self.name, self.value)

        if self.meta_type == "bool":
            if self.value:
                self.raw_meta_entry = "%s = true" % self.name

            else:
                self.raw_meta_entry = "%s = false" % self.name

        self.raw_meta_entry = self.build_comments(
            self.raw_meta_entry, whitespace=whitespace
        )


class YaraMeta:
    """
    Class to represent the YARA meta section

    Attributes:
        meta (OrderedDict): dictionary of YaraMetaEntry objects
        raw_meta (:obj:`list` of :obj:`str`): list of the built meta strings
        number_of_meta_entries (int): the number of meta values overall
            (not necessarily equal to the number of names in the OrderedDict)
        valid_meta_types (:obj:`list` of :obj:`str`): list of valid meta types
        logger (Logger): the logger for this class
    """

    def __init__(self):
        """
        Constructor for YaraMeta
        """
        self.meta = collections.OrderedDict()
        self.raw_meta = []
        self.number_of_meta_entries = 0
        self.valid_meta_types = ["text", "int", "bool"]
        self.logger = logging.getLogger(__name__)

    def add_meta(self, name, value, meta_type="text"):
        """
        Add a YaraMetaEntry to YaraMeta

        Args:
            name (str): the name of the meta entry
            value (str, int, bool): the meta entry
            meta_type (str, optional): the type of the meta entry (defaults to "text")
        """

        if meta_type not in self.valid_meta_types:
            self.logger.warning(
                'Invalid meta_type provided ("%s"), defaulting to "text"', meta_type
            )
            meta_type = "text"

        if name not in self.meta:
            self.meta[name] = []

        self.meta[name].append(
            YaraMetaEntry(name, value, self.number_of_meta_entries, meta_type=meta_type)
        )

        self.number_of_meta_entries += 1

    def build_meta(self, whitespace="    "):
        """
        Build the meta section in the correct order

        Args:
            whitespace (str): whitespace to use when building the meta
        """

        # Allocate an array the size of the number of meta entries
        # This may be larger than the number of meta names,
        # given meta names don't have to be unique
        self.raw_meta = [None] * self.number_of_meta_entries

        for meta_entries in self.meta.values():
            for meta_entry in meta_entries:
                meta_entry.build_meta_entry(whitespace=whitespace)
                self.raw_meta[meta_entry.position] = meta_entry.raw_meta_entry


class YaraString(YaraCommentEnabledClass):
    """
    Class to represent a string object

    Attributes:
        modifiers (:obj:`list` of :obj:`str`): the modifiers applied to the string
        is_anonymous (bool): True if anonymous, False otherwise
        raw_string (str): the built string
        yara_comment (YaraComment): the comment associated with this entry
    """

    def __init__(self, name, value, str_type="text", is_anonymous=False):
        """
        Constructor for YaraString

        Args:
            name (str): the name of the string
            value (str): the value of the string
            str_type (str, optional): the type of the string ("text", "hex", or "regex")
            is_anonymous (bool, optional): bool set to False by default
        """
        self.name = name
        self.value = value
        self.str_type = str_type
        self.modifiers = []
        self.is_anonymous = is_anonymous
        self.raw_string = None
        self.yara_comment = YaraComment()

    def build_string(self, whitespace="    "):
        """
        Build the string (and store in raw_string)

        Args:
            whitespace (str): whitespace to use when building the string
        """
        self.raw_string = "$"

        if not self.is_anonymous:
            self.raw_string += self.name

        self.raw_string += " = "

        if self.str_type == "text":
            self.raw_string += '"%s"' % self.value

        elif self.str_type == "hex":
            self.raw_string += "{%s}" % self.value

        elif self.str_type == "regex":
            self.raw_string += "/%s/" % self.value

        if self.modifiers:
            for modifier in self.modifiers:
                self.raw_string += " %s" % modifier

        self.raw_string = self.build_comments(self.raw_string, whitespace=whitespace)


class YaraStrings:
    """
    Class to represent the YARA strings section

    Attributes:
        raw_strings (:obj:`list` of :obj:`str`): list of the built strings
        strings (OrderedDict): dictionary of the representations of the strings
        number_of_strings (int): total number of strings in the class
        number_of_anonymous_strings (int): number of anonymous string in the class
        valid_str_types (:obj:`list` of :obj:`str`): list of valid str types
        logger (Logger): logger for this class
    """

    def __init__(self):
        """
        Constructor for YaraStrings
        """
        self.raw_strings = []
        self.strings = collections.OrderedDict()
        self.number_of_strings = 0
        self.number_of_anonymous_strings = 0
        self.valid_str_types = ["text", "hex", "regex"]
        self.logger = logging.getLogger(__name__)

    def _invalid_str_type_handler(self, str_type):
        """
        Handler for invalid string types
        Args:
            str_type: the str_type to check if valid

        Returns:
            str: if valid: the original str_type, if invalid: "text"
        """
        if str_type not in self.valid_str_types:
            self.logger.warning(
                'Invalid str_type provided ("%s"), defaulting to "text"', str_type
            )
            str_type = "text"

        return str_type

    def add_string(self, name, value, str_type="text"):
        """
        Add a named string to the YaraStrings object

        Args:
            name (str): name of the string
            value (str): the string
            str_type (str, optional): the type of the string ("text", "hex", "regex")
        """
        if name in self.strings:
            raise ValueError('String with name "{0}" already exists'.format(name))

        str_type = self._invalid_str_type_handler(str_type)

        self.strings[name] = YaraString(name, value, str_type=str_type)
        self.number_of_strings += 1

    def add_anonymous_string(self, value, str_type="text"):
        """
        Add an anonymous string to the YaraStrings object

        Args:
            value (str): the string
            str_type (str, optional): the type of the string ("text", "hex", "regex")

        Returns:
            str: the generated name of the string for later handling
        """
        str_type = self._invalid_str_type_handler(str_type)

        name = "@anon%d" % self.number_of_anonymous_strings
        self.strings[name] = YaraString(
            name, value, str_type=str_type, is_anonymous=True
        )
        self.number_of_strings += 1
        self.number_of_anonymous_strings += 1

        return name

    def add_modifier(self, name, modifier):
        """
        Add a modifier to a string

        Args:
            name (str): the name of the string to add the modifier to
            modifier (str): the modifier to add
        """
        if name not in self.strings:
            raise KeyError("String with name {0} doesn't exist".format(name))

        if self.strings[name].str_type == "hex":
            raise TypeError(
                'String with name {0} is of type "hex", and cannot have modifiers added'.format(
                    name
                )
            )

        if modifier not in self.strings[name].modifiers:
            self.strings[name].modifiers.append(modifier)

    def build_strings(self):
        """
        Build each string object
        """
        for yara_string in self.strings.values():
            yara_string.build_string()
            self.raw_strings.append(yara_string.raw_string)


class YaraCondition:
    """
    Class to represent the YARA condition section

    Attributes:
        raw_condition (str): string representing the built condition

    Todo:
        * Add capabilities to properly add conditions programmatically
    """

    def __init__(self):
        """
        Constructor for YaraCondition
        """
        self.raw_condition = None

    def add_raw_condition(self, raw_condition):
        """
        Add a raw condition

        Args:
            raw_condition (str): the string representing the condition
        """
        self.raw_condition = raw_condition


class YaraImports:
    """
    Class to represent the YARA imports section

    Attributes:
        raw_imports (str): string to represent the built imports
        imports (:obj:`list` of :obj:`str`): list of the imports
    """

    def __init__(self):
        """
        Constructor for YaraImports
        """
        self.raw_imports = ""
        self.imports = []

    def has_imports(self):
        """
        Utility method to determine if there are any imports

        Returns:
            bool: True if there are imports, False otherwise
        """
        if self.imports:
            return True

        return False

    def add_import(self, import_str):
        """
        Add an import to the YaraImports object

        Args:
            import_str (str): the import string to add
        """
        if import_str not in self.imports:
            self.imports.append(import_str)

    def build_imports(self):
        """
        Build the imports section into one string
        """
        for import_str in self.imports:
            self.raw_imports += 'import "%s"\n' % import_str


class YaraTags:
    """
    Class to represent the YARA tags section

    Attributes:
        tags (:obj:`list` of :obj:`str`): list of tags
        raw_tags (str): string representing the built tags
    """

    def __init__(self):
        """
        Constructor for YaraTags
        """
        self.tags = []
        self.raw_tags = ""

    def has_tags(self):
        """
        Utility method to determine if there are any tags

        Returns:
            bool: True if there are tags, False otherwise
        """
        if self.tags:
            return True

        return False

    def add_tag(self, tag):
        """
        Add a tag to the YaraTags object

        Args:
            tag (str): the string representing the tag
        """
        self.tags.append(tag)

    def build_tags(self):
        """
        Build the tags into one string
        """
        self.raw_tags = " ".join(self.tags)


class YaraRule:
    """
    Class to represent a YARA rule

    Attributes:
        rule_name (str): the name of the rule
        logger: logger to use in the class
        raw_rule (str): the "raw" built string representing the YaraRule
        strings (YaraStrings): the strings for this YaraRule
        condition (YaraCondition): the condition for this YaraRule
        imports (YaraImports): the imports for this YaraRule
        tags (YaraTags): the tags for this YaraRule
    """

    def __init__(self, rule_name, whitespace="    ", logger=None):
        """
        Constructor for YaraRule

        Args:
            rule_name (str): the name of the rule to create (every rule has to have a name)
            whitespace (str, optional): whitespace to use when building the rule
                (defaults to 4 spaces)
            logger (optional): logger to use in the class
        """
        self.rule_name = rule_name
        self.whitespace = whitespace

        self.raw_rule = ""
        self.meta = YaraMeta()
        self.strings = YaraStrings()
        self.condition = YaraCondition()
        self.imports = YaraImports()
        self.tags = YaraTags()

        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

    def build_rule_header(self, rule):
        """
        Method to build the rule header, including the imports, tags and rule_name

        Args:
            rule (str): string of the rule built so far

        Returns:
            str: string of the built rule with added rule header
        """
        if self.imports.has_imports():
            self.imports.build_imports()
            rule += "%s\n" % self.imports.raw_imports

        if self.tags.has_tags():
            self.tags.build_tags()
            rule += "rule %s : %s {\n" % (self.rule_name, self.tags.raw_tags)
        else:
            rule += "rule %s {\n" % self.rule_name

        return rule

    def build_rule_condition_section(self, rule):
        """
        Method to build the rule condition section

        Args:
            rule (str): string of the rule built so far

        Returns:
            str: string of the built rule with added rule condition
        """
        rule += "%scondition:\n" % self.whitespace
        rule += "%s%s%s\n" % (
            self.whitespace,
            self.whitespace,
            self.condition.raw_condition,
        )
        rule += "}"

        return rule

    def build_rule_strings_section(self, rule):
        """
        Method to build the rule strings section

        Args:
            rule (str): string of the rule built so far

        Returns:
            str: string of the built rule with added rule strings
        """
        self.strings.build_strings()

        rule += "%sstrings:\n" % self.whitespace

        for raw_string in self.strings.raw_strings:
            rule += "%s%s%s\n" % (self.whitespace, self.whitespace, raw_string)

        rule += "\n"

        return rule

    def build_rule_meta_section(self, rule):
        """
        Method to build the rule meta section

        Args:
            rule (str): string of the rule built so far

        Returns:
            str: string of the built rule with added rule meta
        """
        self.meta.build_meta(whitespace=self.whitespace)

        rule += "%smeta:\n" % self.whitespace

        for raw_meta_entry in self.meta.raw_meta:
            rule += "%s%s%s\n" % (self.whitespace, self.whitespace, raw_meta_entry)

        rule += "\n"

        return rule

    def build_rule(self):
        """
        Method to build the whole YARA rule

        Returns:
            str: the string of the built rule
        """
        if not self.condition.raw_condition:
            raise KeyError(
                '"{0}" has no raw_condition, cannot build rule'.format(self.rule_name)
            )

        self.raw_rule = self.build_rule_header(self.raw_rule)

        if self.meta.number_of_meta_entries > 0:
            self.raw_rule = self.build_rule_meta_section(self.raw_rule)

        if self.strings.number_of_strings > 0:
            self.raw_rule = self.build_rule_strings_section(self.raw_rule)

        self.raw_rule = self.build_rule_condition_section(self.raw_rule)

        return self.raw_rule


def main():  # pragma: no cover
    """
    Method to test if running the module from the command line
    """
    rule = YaraRule("command_line_rule")
    rule.condition.add_raw_condition("filesize > 0")
    rule.tags.add_tag("test1")
    rule.tags.add_tag("test2")
    rule.imports.add_import("pe")
    rule.imports.add_import("math")
    rule.meta.add_meta("test_meta", "test1")
    rule.meta.add_meta("test_meta", "test2")
    rule.meta.meta["test_meta"][0].add_comment("hi", position="above")
    rule.meta.meta["test_meta"][1].add_comment("there", position="above")
    rule.strings.add_string("test_string_text", "string_text_val")
    rule.strings.add_modifier("test_string_text", "ascii")
    rule.strings.strings["test_string_text"].add_comment("above comment")
    rule.strings.strings["test_string_text"].add_comment(
        "inline comment", position="inline"
    )
    rule.strings.strings["test_string_text"].add_comment(
        "below comment", position="below"
    )
    rule.strings.add_string("test_string_hex", "AA BB CC DD", str_type="hex")
    rule.strings.add_string("test_string_regex", "[0-9]{10}", str_type="regex")
    print(rule.build_rule())


if __name__ == "__main__":  # pragma: no cover
    main()
