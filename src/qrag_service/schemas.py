from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=256)
    text: str = Field(min_length=1, max_length=12000)


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=2000)
    sources: list[Source] = Field(min_length=1, max_length=100)
    methods: list[Literal["relevance", "milp", "mmr", "qaoa"]] = Field(
        default_factory=lambda: ["relevance", "milp"], min_length=1, max_length=4
    )
    k: int = Field(default=3, ge=1, le=10, strict=True)
    allow_classical_fallback: bool = True
    deadline_seconds: float = Field(default=60, ge=1, le=120)

    @model_validator(mode="after")
    def validate_pool(self):
        if len({s.id for s in self.sources}) != len(self.sources):
            raise ValueError("Source IDs must be unique")
        if len(set(self.methods)) != len(self.methods):
            raise ValueError("Methods must be unique")
        if self.k > len(self.sources):
            raise ValueError("k exceeds the available source count")
        if sum(len(s.text) for s in self.sources) > 100000:
            raise ValueError("Combined source text exceeds 100,000 characters")
        return self


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    corpus: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,40}$")
    sources: list[Source] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_size(self):
        if sum(len(s.text) for s in self.sources) > 1000000:
            raise ValueError("Corpus text exceeds one million characters")
        if len({s.id for s in self.sources}) != len(self.sources):
            raise ValueError("Source IDs must be unique")
        return self


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    corpus: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,40}$")
    question: str = Field(min_length=1, max_length=2000)
    candidates: int = Field(default=20, ge=1, le=100, strict=True)
    retrieval: Literal["dense", "bm25", "hybrid"] = "hybrid"
    methods: list[Literal["relevance", "milp", "mmr", "qaoa"]] = Field(
        default_factory=lambda: ["relevance", "milp"], min_length=1, max_length=4
    )
    k: int = Field(default=3, ge=1, le=10, strict=True)
    allow_classical_fallback: bool = True
    deadline_seconds: float = Field(default=60, ge=1, le=120)

    @model_validator(mode="after")
    def validate_count(self):
        if self.k > self.candidates:
            raise ValueError("k exceeds requested candidate count")
        if len(set(self.methods)) != len(self.methods):
            raise ValueError("Methods must be unique")
        return self
