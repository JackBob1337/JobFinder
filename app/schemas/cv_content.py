from pydantic import BaseModel

class CVEntry(BaseModel):
    title: str
    stack: list[str] = []
    bullets: list[str] = []

class CVContent(BaseModel):
    summary: str
    experience: list[CVEntry]
    projects: list[CVEntry]
    location: str | None = None

    def as_text(self) -> str:
        parts = ["PROFESSIONAL SUMMARY:", self.summary]

        parts.append("\nEXPERIENCE:")
        for entry in self.experience:
            parts.append(entry.title)
            parts.extend(f"- {b}" for b in entry.bullets)

        parts.append("\nPROJECTS:")
        for entry in self.projects:
            parts.append(entry.title)
            parts.extend(f"- {b}" for b in entry.bullets)

        return "\n".join(parts)