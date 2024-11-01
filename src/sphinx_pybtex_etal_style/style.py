"""Style definition for :code:`unsrt_etal`."""

# pyright: reportMissingTypeStubs=false
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pybtex.richtext import Tag, Text
from pybtex.style.formatting.unsrt import Style as UnsrtStyle
from pybtex.style.template import (
    FieldIsMissing,
    Node,
    _format_list,  # pyright: ignore[reportPrivateUsage]  # noqa: PLC2701
    field,
    href,
    join,
    node,
    sentence,
    words,
)

if TYPE_CHECKING:
    from pybtex.database import Entry


ISBNResolvers = Literal["bookfinder", "isbnsearch"]


# Specify bibliography style
@node
def et_al(children, data, sep="", sep2=None, last_sep=None):  # type: ignore[no-untyped-def]
    if sep2 is None:
        sep2 = sep
    if last_sep is None:
        last_sep = sep
    parts = [part for part in _format_list(children, data) if part]
    if len(parts) <= 1:
        return Text(*parts)
    if len(parts) == 2:  # noqa: PLR2004
        return Text(sep2).join(parts)
    if len(parts) == 3:  # noqa: PLR2004
        return Text(last_sep).join([Text(sep).join(parts[:-1]), parts[-1]])
    return Text(parts[0], Tag("em", " et al"))


@node
def names(children, context, role, **kwargs):  # type: ignore[no-untyped-def]
    """Return formatted names."""
    if children:
        msg = "The names field should not contain any children"
        raise ValueError(msg)
    try:
        persons = context["entry"].persons[role]
    except KeyError as exc:
        raise FieldIsMissing(role, context["entry"]) from exc

    style = context["style"]
    formatted_names = [
        style.format_name(person, style.abbreviate_names) for person in persons
    ]
    return et_al(**kwargs)[  # pyright: ignore[reportUntypedBaseClass]
        formatted_names
    ].format_data(context)


class UnsrtEtAl(UnsrtStyle):
    isbn_resolver: ClassVar[ISBNResolvers] = "bookfinder"

    def __init__(self) -> None:
        super().__init__(abbreviate_names=True)

    def format_names(self, role: Entry, as_sentence: bool = True) -> Node:  # noqa: PLR6301
        formatted_names = names(role, sep=", ", sep2=" and ", last_sep=", and ")
        if as_sentence:
            return sentence[formatted_names]
        return formatted_names

    def format_eprint(self, e: Entry) -> Node:
        if "doi" in e.fields:  # pyright:ignore[reportOperatorIssue]
            return ""  # pyright:ignore[reportReturnType]
        return super().format_eprint(e)

    def format_url(self, e: Entry) -> Node:  # noqa: PLR6301
        if "doi" in e.fields or "eprint" in e.fields:  # pyright:ignore[reportOperatorIssue]
            return ""  # pyright:ignore[reportReturnType]
        return words[
            href[
                field("url", raw=True),
                field("url", raw=True, apply_func=remove_http),
            ]
        ]

    def format_isbn(self, e: Entry) -> Node:  # noqa: ARG002
        raw_isbn = field("isbn", raw=True, apply_func=remove_dashes_and_spaces)
        if self.isbn_resolver == "bookfinder":
            url = join[
                "https://www.bookfinder.com/search/?isbn=",
                raw_isbn,
                "&mode=isbn&st=sr&ac=qr",
            ]
        elif self.isbn_resolver == "isbnsearch":
            url = join["https://isbnsearch.org/isbn/", raw_isbn]
        else:
            msg = (
                f"Unknown unsrt_etal_isbn_resolver: {self.isbn_resolver}. Valid options"
                f" are {', '.join(ISBNResolvers.__args__)}."
            )
            raise NotImplementedError(msg)
        return href[url, join["ISBN:", field("isbn", raw=True)]]


def remove_dashes_and_spaces(isbn: str) -> str:
    to_remove = ["-", " "]
    for remove in to_remove:
        isbn = isbn.replace(remove, "")
    return isbn


def remove_http(url: str) -> str:
    to_remove = ["https://", "http://"]
    for remove in to_remove:
        url = url.replace(remove, "")
    return url
