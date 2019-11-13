import inspect
from functools import partial
from pathlib import Path
from typing import List, Union, Callable

import libcst as cst
import black
from black import reformat_one, FileMode, Report, WriteBack, Changed
from libcst import CSTNodeT, RemovalSentinel, MetadataWrapper
from libcst.metadata import PositionProvider

from pyautodev.modifiers import CommentWrap

MAX_LINE_LENGTH = black.DEFAULT_LINE_LENGTH


class Black:
    def __init__(self):
        self._mode = FileMode.from_configuration(
            py36=False,
            pyi=False,
            skip_string_normalization=False,
            skip_numeric_underscore_normalization=False,
        )

    def transform(self, filepaths: List[str]):
        report = Black.CollectingReport()
        for filepath in filepaths:
            reformat_one(
                src=Path(filepath),
                line_length=MAX_LINE_LENGTH,
                fast=False,
                write_back=WriteBack.YES,
                mode=self._mode,
                report=report,
            )
        return report

    class CollectingReport(Report):
        def __init__(self):
            self.done_paths_changed = {}
            self.failed_paths_msg = {}

        def done(self, src: Path, changed: Changed) -> None:
            self.done_paths_changed[src] = changed

        def failed(self, src: Path, message: str):
            self.failed_paths_msg[src] = message


class PyAutoDev(cst.CSTTransformer):

    METADATA_DEPENDENCIES = (PositionProvider,)
    _DEFAULT_MODIFIERS = [CommentWrap()]

    def __init__(self, modifiers=None):
        super().__init__()
        self._modifiers = modifiers or self._DEFAULT_MODIFIERS
        self._init_leave_methods()

    def transform(self, filepaths: List[str]):
        for filepath in filepaths:

            with open(filepath, "r") as f:
                orig_contents = MetadataWrapper(cst.parse_module(f.read()))

            updated_contents = orig_contents.visit(self)

            with open(filepath, "w") as f:
                f.write(updated_contents.code)

    def _init_leave_methods(self):
        modifier_leave_methods = {}
        for m in self._modifiers:
            setattr(m, 'get_metadata', self.get_metadata)
            for name, value in vars(m.__class__).items():
                if inspect.isroutine(value) and name.startswith("leave_"):
                    if name not in modifier_leave_methods:
                        modifier_leave_methods[name] = []
                    modifier_leave_methods[name].append(partial(value, m))

        for fn_name, modifier_leave_fns in modifier_leave_methods.items():
            leave_fn = partial(self._leave_node, modifier_leave_fns=modifier_leave_fns)
            setattr(self, fn_name, leave_fn)

    def _leave_node(
        self,
        original_node: CSTNodeT,
        updated_node: CSTNodeT,
        modifier_leave_fns: List[Callable],
    ) -> Union[CSTNodeT, RemovalSentinel]:
        for modifier_leave_fn in modifier_leave_fns:
            updated_node = modifier_leave_fn(original_node, updated_node)
            if updated_node == RemovalSentinel:
                return updated_node
        return updated_node
