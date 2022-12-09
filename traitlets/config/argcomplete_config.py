import argparse
import typing as t

import argcomplete


class ExtendedCompletionFinder(argcomplete.CompletionFinder):
    """An extension of CompletionFinder which dynamically completes class-trait based options

    This finder mainly adds 2 functionalities:

    1. When completing options, it will add --Class. to the list of completions, for each
    class in Application.classes that could complete the current option.
    2. If it detects that we are currently trying to complete an option related to --Class.,
    it will add the corresponding config traits of Class to the ArgumentParser instance,
    so that the traits' completers can be used.

    Note that we are avoiding adding all config traits of all classes to the ArgumentParser,
    which would be easier but would add more runtime overhead and would also make completions
    appear more spammy.

    These changes do require using the internals of argcomplete.CompletionFinder.
    """

    _parser: argparse.ArgumentParser
    config_classes: t.List[t.Any]  # Configurables

    def match_class_completions(self, cword_prefix: str) -> t.List[t.Tuple[t.Any, str]]:
        """Match the word to be completed against our Configurable classes

        Check if cword_prefix could potentially match against --{class}. for any class
        in Application.classes.
        """
        class_completions = [(cls, f"--{cls.__name__}.") for cls in self.config_classes]
        matched_completions = class_completions
        if "." in cword_prefix:
            cword_prefix = cword_prefix[: cword_prefix.index(".") + 1]
            matched_completions = [(cls, c) for (cls, c) in class_completions if c == cword_prefix]
        elif len(cword_prefix) > 0:
            matched_completions = [
                (cls, c) for (cls, c) in class_completions if c.startswith(cword_prefix)
            ]
        return matched_completions

    def inject_class_to_parser(self, cls):
        """Add dummy arguments to our ArgumentParser for the traits of this class

        The argparse-based loader currently does not actually add any class traits to
        the constructed ArgumentParser, only the flags & aliaes. In order to work nicely
        with argcomplete's completers functionality, this method adds dummy arguments
        of the form --Class.trait to the ArgumentParser instance.

        This method should be called selectively to reduce runtime overhead and to avoid
        spamming options across all of Application.classes.
        """
        try:
            for traitname, trait in cls.class_traits(config=True).items():
                completer = trait.metadata.get("argcompleter") or getattr(
                    trait, "argcompleter", None
                )
                multiplicity = trait.metadata.get("multiplicity")
                self._parser.add_argument(
                    f"--{cls.__name__}.{traitname}",
                    type=str,
                    help=trait.help,
                    nargs=multiplicity,
                    # metavar=traitname,
                ).completer = completer  # type: ignore
                argcomplete.debug(f"added --{cls.__name__}.{traitname}")
        except AttributeError:
            pass

    def _get_completions(self, comp_words: t.List[str], cword_prefix: str, *args) -> t.List[str]:
        """Overriden to dynamically append --Class.trait arguments if appropriate

        Warning:
            This does not (currently) support completions of the form
            --Class1.Class2.<...>.trait, although this is valid for traitlets.
            Part of the reason is that we don't currently have a way to identify
            which classes may be used with Class1 as a parent.

        Warning:
            This is an internal method in CompletionFinder and so the API might
            be subject to drift.
        """
        # Try to identify if we are completing something related to --Class. for
        # a known Class, if we are then add the Class config traits to our ArgumentParser.
        prefix_chars = self._parser.prefix_chars
        is_option = len(cword_prefix) > 0 and cword_prefix[0] in prefix_chars
        if is_option:
            # If we are currently completing an option, check if it could
            # match with any of the --Class. completions. If there's exactly
            # one matched class, then expand out the --Class.trait options.
            matched_completions = self.match_class_completions(cword_prefix)
            if len(matched_completions) == 1:
                matched_cls = matched_completions[0][0]
                self.inject_class_to_parser(matched_cls)
        elif len(comp_words) > 0 and "." in comp_words[-1] and not is_option:
            # If not an option, perform a hacky check to see if we are completing
            # an argument for an already present --Class.trait option. Search backwards
            # for last option (based on last word starting with prefix_chars), and see
            # if it is of the form --Class.trait. Note that if multiplicity="+", these
            # arguments might conflict with positional arguments.
            for prev_word in comp_words[::-1]:
                if len(prev_word) > 0 and prev_word[0] in prefix_chars:
                    matched_completions = self.match_class_completions(prev_word)
                    if matched_completions:
                        matched_cls = matched_completions[0][0]
                        self.inject_class_to_parser(matched_cls)
                    break

        return super()._get_completions(comp_words, cword_prefix, *args)

    def _get_option_completions(
        self, parser: argparse.ArgumentParser, cword_prefix: str
    ) -> t.List[str]:
        """Overriden to add --Class. completions when appropriate"""
        completions = super()._get_option_completions(parser, cword_prefix)
        if cword_prefix.endswith("."):
            return completions

        matched_completions = self.match_class_completions(cword_prefix)
        if len(matched_completions) > 1:
            completions.extend(opt for cls, opt in matched_completions)
        # If there is exactly one match, we would expect it to have aleady
        # been handled by the options dynamically added in _get_completions().
        # However, maybe there's an edge cases missed here, for example if the
        # matched class has no configurable traits.
        return completions
