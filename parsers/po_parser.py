from __future__ import annotations

from pathlib import Path

import polib

from .base import BaseParser


class PoParser(BaseParser):
    def load(self, path: Path) -> dict[str, str]:
        po = polib.pofile(str(path))
        return {entry.msgid: entry.msgstr for entry in po if entry.msgid}

    def save(self, path: Path, data: dict[str, str]) -> None:
        try:
            po = polib.pofile(str(path))
        except Exception:
            po = polib.POFile()
            po.metadata = {"Content-Type": "text/plain; charset=UTF-8"}

        existing = {entry.msgid: entry for entry in po}
        for msgid, msgstr in data.items():
            if msgid in existing:
                existing[msgid].msgstr = msgstr
            else:
                po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))

        po[:] = [e for e in po if e.msgid in data]
        po.save(str(path))
