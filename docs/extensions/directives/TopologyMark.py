from __future__ import annotations

import yaml
from pytest_mh import TopologyMark
from sphinx.directives.code import CodeBlock

from authselect_test_framework.topology import Profile, ProfileGroup


class TopologyMarkDirective(CodeBlock):
    """
    Render :class:`TopologyMark` values as YAML inside a code block.
    """

    def run(self):
        obj = eval(self.arguments[0])
        if isinstance(obj, Profile):
            self.content = self.export(obj.value)
        elif isinstance(obj, ProfileGroup):
            out = []
            for profile in obj.value:
                out += self.export(profile.value) + [""]
            self.content = out
        elif isinstance(obj, TopologyMark):
            self.content = self.export(obj)
        else:
            raise ValueError(f"Invalid argument: {self.arguments[0]}")

        self.arguments[0] = "yaml"

        return super().run()

    def export(self, mark: TopologyMark) -> list[str]:
        return yaml.dump(mark.export(), sort_keys=False).splitlines()


def setup(app):
    app.add_directive("topology-mark", TopologyMarkDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }