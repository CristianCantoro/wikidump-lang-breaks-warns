"""
WIKIBREAKS DOCUMENTATION
There are many wikibreaks templates as I can see:
https://en.wikipedia.org/wiki/Template:Wikibreak:
# Basics attributes I need to scrape
{{wikibreak | [Name] | back = | type = | message  = | align = | image = | noimage = | imagesize = | spacetype = | style = }}
# to consider {{in-house switch}} {{At school}} {{Exams}} {{Vacation}} {{Out of town}} {{Personal issues}}
"""

import regex as re
from .. import wikibreaks
from typing import Iterable, Iterator
from .common import CaptureResult
from .types.wikibreak import Wikibreak
from mwtemplates import TemplateEditor

# NOTE
# Strange behaviours: 
# {{wikibreak|name=Samuele|Mario}}, only Samuele is displayed
# {{wikibreak|Samuele|Mario}}, while in this case Mario is considered as a back value
# So remember, the positional arguments are weaker than the named ones
# {{wikibreak|name=Samuele|ciao|come va|type=epico|back=10/10/2020|lol}}
# Seen as
# name          name pos   1(ov) 2(ov)                              3
# Where ov means overridden

# exports 
__all__ = ['wikibreaks_extractor', 'Wikibreak', ]

# https://regex101.com/r/BK0q6s/1
wikibreak_pattern = r'''
    \{\{                    # match {{
        (?:                 # non-capturing group
            \s              # match any spaces
            |               # or
            \_              # match underscore (count as space)
        )*                  # match 0 or multiple times
        (?P<type>           # namedgroup named type
            %s              # wikibreak word to substitute
        )                   # closed named group
        (?:                 # start of a non capturing group
            \s              # match any spaces
            |               # or
            \_              # match _
        )*                  # repeat the group 0 or n times
        \|                  # match pipe
        (?P<options>        # named group options
            [^{]*           # match anything but closed curly brakets
        )                   # end of the named group
    \}\}'''                 # match }}

# https://regex101.com/r/Cuey3K/1
wikibreak_empty_pattern = r'''
    \{\{                    # match {{
        (?:                 # non-capturing group
            \s              # match any spaces
            |               # or
            \_              # match underscore (count as space)
        )*                  # match 0 or multiple times
        (?P<type>           # named group named type
            %s              # wikibreak word to substitute
        )                   # closed named group
        (?P<options>        # named group named options
            (?:             # non-capturing group
                \s          # match any spaces
                |           # or
                \_          # match _
            )*              # repeat the group 0 or n times
        )                   # end of a non captuiring group
    \}\}'''                 # match }}

# BACK/NOT CATEGORY 
wikibreak_back_not_words = wikibreaks.wikibreak_cant_retire + \
    wikibreaks.wikibreak_considering_retirement + \
    wikibreaks.wikibreak_off_and_on

# BREAK CATEGORY
wikibreak_words = wikibreaks.wikibreak_standard_words + \
    wikibreaks.wikibreak_in_house + \
    wikibreaks.wikibreak_switch + \
    wikibreaks.wikibreak_at_school + \
    wikibreaks.wikibreak_exams + \
    wikibreaks.wikibreak_vacation + \
    wikibreaks.wikibreak_out_of_town + \
    wikibreaks.wikibreak_personal_issue

# HEALTH-RELATED
wikibreak_health_words = wikibreaks.wikibreak_user_bonked + \
    wikibreaks.wikibreak_user_grieving + \
    wikibreaks.wikibreak_user_health_inactive + \
    wikibreaks.wikibreak_user_covid19

# MENTAL
wikibreak_mental_words = wikibreaks.wikibreak_busy + \
    wikibreaks.wikibreak_discouraged + \
    wikibreaks.wikibreak_user_contempt + \
    wikibreaks.wikibreak_user_frustrated

# HEALTH-RELATED AND MENTAL
wikibreak_health_mental_words = wikibreaks.wikibreak_user_stress + \
    wikibreaks.wikibreak_user_mental_health

# TECHNICAL
wikibreak_technical_words = wikibreaks.wikibreak_computer_death + \
    wikibreaks.wikibreak_no_internet + \
    wikibreaks.wikibreak_no_power + \
    wikibreaks.wikibreak_storm_break

# OTHER
wikibreak_other_words = wikibreaks.wikibreak_deceased + \
    wikibreaks.wikibreak_not_around + \
    wikibreaks.wikibreak_retired + \
    wikibreaks.wikibreak_semi_retired + \
    wikibreaks.wikibreak_userbox_ex_wikipedia

# ALL
all_wikibreaks_words = wikibreak_back_not_words + \
    wikibreak_words + \
    wikibreak_health_words + \
    wikibreak_mental_words + \
    wikibreak_health_mental_words + \
    wikibreak_technical_words + \
    wikibreak_other_words

WIKIBREAKS_PATTERN_REs = [ 
    re.compile(wikibreak_pattern%(w_word.replace(' ', '\ ')), re.IGNORECASE | re.UNICODE | re.VERBOSE | re.MULTILINE) 
    for w_word in all_wikibreaks_words
]

WIKIBREAKS_EMPTY_PATTERN_REs = [
    re.compile(wikibreak_empty_pattern%(w_word.replace(' ', '\ ')), re.IGNORECASE | re.UNICODE | re.VERBOSE | re.MULTILINE) 
    for w_word in all_wikibreaks_words
]

WIKIBREAKS_REs = WIKIBREAKS_PATTERN_REs + WIKIBREAKS_EMPTY_PATTERN_REs

def wikibreaks_extractor(text: str) -> Iterator[CaptureResult[Wikibreak]]:

    # use template extractor from mwtemplates
    try:
        wbreaks = TemplateEditor(text)
    except:
        # there can be different type of text which are not supported by mwtemplates
        return wikibreaks_extractor_handcrafted(text)

    # for each unique template name
    for key in wbreaks.templates.keys():

        wiki_name = key.lower().strip()
        # check if the template is one of the desired ones
        if not wiki_name in all_wikibreaks_words:
            continue

        # for each template named key occurence
        for template in wbreaks.templates[key]:

            # basic parameters
            wikimap = wikibreaks.wikibreak_fields_to_tuple_category_subcategory[wiki_name]
            wiki_category = wikimap['category']
            wiki_sub_category = wikimap['subcategory']
            wikibreak_obj = Wikibreak(wiki_name, wiki_category, wiki_sub_category, dict(), False)

            # Counter for positional arguments
            positional_counter = 1  # NOTE: starting from 1, as the first argument is 1 in the wikimarkup

            # for each parameter
            for i, parameters in enumerate(template.parameters):
                
                # named parameter
                if len(parameters.name.strip()) > 0:
                    wikibreak_obj.options[parameters.name.strip()] = parameters.value
                else:
                    # positional parameter
                    wikibreak_obj.options[positional_counter] = parameters.value
                    positional_counter += 1

                wikibreak_obj.at_least_one_parameter = True

            yield CaptureResult(
                data=(wikibreak_obj), span=None
            )

def wikibreaks_extractor_handcrafted(text: str) -> Iterator[CaptureResult[Wikibreak]]:
    for pattern in WIKIBREAKS_REs:
        for match in pattern.finditer(text): # returns an iterator of match object
            if check_wikibreaks_presence(match): # extract a named group called type (name of the wikipause template used)
                wiki_name = match.group('type')
                
                if not wiki_name:
                    return
                
                # Wikipause object: basically the name and the list of options
                wiki_name = wiki_name.lower()
                wikimap = wikibreaks.wikibreak_fields_to_tuple_category_subcategory[wiki_name]
                wiki_category = wikimap['category']
                wiki_sub_category = wikimap['subcategory']
                wikibreak_obj = Wikibreak(wiki_name, wiki_category, wiki_sub_category, dict(), False)

                # Parse the options if any
                if check_options(match):
                    # parse the options
                    parsed_options = match.group('options').strip().replace('_', '') # retrieve the options
                    # threat differently the wikilinks in it
                    parsed_options = split_and_adjust_wikilinks(parsed_options)

                    # Counter for positional arguments
                    positional_counter = 1  # NOTE: starting from 1, as the first argument is 1 in the wikimarkup

                    # if no options are provided (note empty options means {{wikibreak}} and not {{wikibreak|}} nor {{wikibreak||}})
                    # those last two are considered as options are actually passed
                    if not (len(parsed_options) == 1 and parsed_options[0] == ''):
                        # loop over all the parsed options
                        for opt in parsed_options:
                            # Splitting for namedparameters -> note there is no way I can store all the possibile way to call a parameter, 
                            # due to lack of documentation and other things
                            name_value = opt.split('=', 1)
                            # Key and value for the option entry in the dictionary
                            key = positional_counter
                            value = name_value[0]
                            if len(name_value) > 1:
                                key, value = name_value
                            else:
                                positional_counter += 1
                            # Assign the parsed options to the wikibreak_obj
                            wikibreak_obj.options[key] = value  # overritten in case of the same name of the parameters
                        # at least one parameter found
                        wikibreak_obj.at_least_one_parameter = True

                yield CaptureResult(
                    data=(wikibreak_obj), span=(match.start(), match.end())
                )

# https://stackoverflow.com/questions/42070323/split-on-spaces-not-inside-parentheses-in-python
def split_and_adjust_wikilinks(sentence: str, separator: str = "|", lparen: str = "[", rparen:str = "]") -> Iterable[str]:
    """
    Simple wikilinks detector and handler for cases where there are wikilinks in wikibreaks
    E.g:
    {{wikibreak|[[User:Foo|Foobar]]|motivation}}
    The options should be parsed as:
    1) [[Uesr:Foo|Foobar]] # wikilink detected!
    2) motivation
    And should also be individuated the following:
    name|[[26 agosto]],''[[Villasimius|a Villasimius]]'',[[Austria |a Vienna]] .
    """
    nb_brackets = 0
    sentence = sentence.strip(separator) # get rid of leading/trailing seps
    l = [0]
    for i,c in enumerate(sentence):
        if c == lparen:
            nb_brackets += 1
        elif c == rparen:
            nb_brackets -= 1
        elif c == separator and nb_brackets == 0:
            l.append(i)
    l.append(len(sentence))
    return([sentence[i:j].strip(separator) for i,j in zip(l,l[1:])])

def concatenate_list_values(elem_list: Iterable[str], from_index: int, to_index, concatenate_value: str) -> str:
    """Concatenates element in a list of strings starting from a starting index until the end index (included) with a custom separator"""
    result = elem_list[from_index] 
    for i in range(from_index + 1, to_index + 1):
        result += '{}{}'.format(concatenate_value, elem_list[i])
    return result

def check_options(match: Iterator[re.Match]) -> bool:
    """Checks if some groups is present inside the match object"""
    try:
        match.group('options')
        return True
    except IndexError:
        return False

def check_wikibreaks_presence(match: Iterator[re.Match]) -> bool:
    """Checks if some groups is present inside the match object"""
    try:
        match.group('type')
        return True
    except IndexError:
        return False