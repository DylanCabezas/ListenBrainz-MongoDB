from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request, Response

from app.models import ArtistResponse, ListenCreate, ListenFeed, ListenPage, ListenResponse, ListenUpdate, SummaryResponse
from app.services.listen_service import ListenService, build_filter


router = APIRouter(prefix="/listens", tags=["Listens"])


def get_service(request: Request):
    return ListenService(request.app.state.collection)


def get_filters(
    user_name: Annotated[str | None, Query(min_length=1, max_length=1000)] = None,
    artist_name: Annotated[str | None, Query(min_length=1, max_length=1000)] = None,
    start_timestamp: Annotated[int | None, Query(ge=0, le=253402300799)] = None,
    end_timestamp: Annotated[int | None, Query(ge=0, le=253402300799)] = None,
):
    return build_filter(user_name, artist_name, start_timestamp, end_timestamp)


Service = Annotated[ListenService, Depends(get_service)]
Filters = Annotated[dict, Depends(get_filters)]


@router.post("", response_model=ListenResponse, status_code=201)
def create_listen(payload: ListenCreate, service: Service):
    return service.create_listen(payload)


@router.get("", response_model=ListenPage)
def list_listens(
    service: Service, query: Filters,
    page: Annotated[int, Query(ge=1, le=10000)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    sort_by: Literal["timestamp", "user_name", "track_metadata.artist_name"] = "timestamp",
    sort_order: Literal["asc", "desc"] = "desc",
):
    return service.list_listens(query, page, limit, sort_by, sort_order)


@router.get("/stats/summary", response_model=SummaryResponse)
def get_summary(service: Service, query: Filters):
    return service.get_summary(query)


@router.get("/stats/top-artists", response_model=list[ArtistResponse])
def get_top_artists(service: Service, query: Filters, limit: Annotated[int, Query(ge=1, le=100)] = 10):
    return service.get_top_artists(query, limit)


@router.get("/feed", response_model=ListenFeed)
def get_listen_feed(
    service: Service, query: Filters,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query(min_length=1, max_length=1000)] = None,
):
    return service.get_listen_feed(query, limit, cursor)


@router.get("/{listen_id}", response_model=ListenResponse)
def get_listen(listen_id: str, service: Service):
    return service.get_listen(listen_id)


@router.patch("/{listen_id}", response_model=ListenResponse)
def update_listen(listen_id: str, payload: ListenUpdate, service: Service):
    return service.update_listen(listen_id, payload)


@router.put("/{listen_id}", response_model=ListenResponse)
def replace_listen(listen_id: str, payload: ListenCreate, service: Service):
    return service.replace_listen(listen_id, payload)


@router.delete("/{listen_id}", status_code=204)
def delete_listen(listen_id: str, service: Service):
    service.delete_listen(listen_id)
    return Response(status_code=204)
