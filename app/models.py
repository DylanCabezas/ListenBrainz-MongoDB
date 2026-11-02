from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, model_validator
from typing_extensions import Annotated


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
Timestamp = Annotated[StrictInt, Field(ge=0, le=253402300799)]


def validate_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or key.startswith("$") or "." in key or "\x00" in key:
                raise ValueError("Metadata keys must not contain dots, null bytes or start with $")
            validate_keys(item)
    elif isinstance(value, list):
        for item in value:
            validate_keys(item)
    return value


class MetadataBase(BaseModel):
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def validate_metadata_keys(cls, value):
        return validate_keys(value)


class TrackMetadata(MetadataBase):
    track_name: Name
    artist_name: Name
    release_name: str | None = None
    additional_info: dict[str, Any] = Field(default_factory=dict)


class ListenCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_name: Name
    timestamp: Timestamp
    track_metadata: TrackMetadata
    user_id: int | None = None
    recording_msid: str | None = None


class TrackMetadataUpdate(MetadataBase):
    track_name: Name | None = None
    artist_name: Name | None = None
    release_name: str | None = None
    additional_info: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one metadata field")
        for key in ("track_name", "artist_name", "additional_info"):
            if key in self.model_fields_set and getattr(self, key) is None:
                raise ValueError(f"{key} must not be null")
        return self


class ListenUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_name: Name | None = None
    timestamp: Timestamp | None = None
    track_metadata: TrackMetadataUpdate | None = None

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set or any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError("Provide at least one non-null field")
        return self


class ListenResponse(ListenCreate):
    model_config = ConfigDict(extra="ignore")
    id: str


class ListenPage(BaseModel):
    items: list[ListenResponse]
    page: int
    limit: int
    total: int


class SummaryResponse(BaseModel):
    total_listens: int
    unique_users: int


class ListenCursor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timestamp: Timestamp
    id: str
    id_type: Literal["objectId", "string"]


class ListenFeed(BaseModel):
    items: list[ListenResponse]
    next_cursor: str | None


class ArtistResponse(BaseModel):
    artist_name: str
    listen_count: int
