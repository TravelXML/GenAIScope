"""Memory REST API routes."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse

from genaiscope.server.schemas import (
    ContextRequest,
    ContextResponse,
    PromptRequest,
    RememberRequest,
    SearchRequest,
    SearchResultItem,
)


def add_memory_routes(app: Any, store: Any, auth_dep: Any) -> None:
    @app.get("/v1/memory/stats")
    async def stats(_: Any = Depends(auth_dep)) -> JSONResponse:
        return JSONResponse(store.stats().model_dump())

    @app.post("/v1/memory/remember")
    async def remember(req: RememberRequest, _: Any = Depends(auth_dep)) -> JSONResponse:
        item = store.add(
            content=req.content,
            memory_type=req.memory_type,
            user_id=req.user_id,
            project_id=req.project_id,
            workspace_id=req.workspace_id,
            agent_id=req.agent_id,
            session_id=req.session_id,
            tags=req.tags,
            importance=req.importance,
            ttl_days=req.ttl_days,
            metadata=req.metadata,
        )
        return JSONResponse({"id": item.id, "memory_type": item.memory_type, "content": item.content})

    @app.post("/v1/memory/search")
    async def search(req: SearchRequest, _: Any = Depends(auth_dep)) -> JSONResponse:
        kw: dict[str, Any] = {
            "limit": req.limit, "mode": req.mode,
            "user_id": req.user_id, "project_id": req.project_id, "workspace_id": req.workspace_id,
        }
        if req.memory_type:
            kw["memory_type"] = req.memory_type
        results = store.search(req.query, **kw)
        return JSONResponse({
            "results": [
                SearchResultItem(
                    id=r.item.id, content=r.item.content, score=r.score,
                    match_type=r.match_type, ranking_reason=r.ranking_reason,
                    memory_type=r.item.memory_type,
                    keyword_score=r.keyword_score,
                    vector_score=r.vector_score,
                    fused_score=r.fused_score,
                    embedder_name=r.embedder_name,
                ).model_dump()
                for r in results
            ]
        })

    @app.post("/v1/memory/context")
    async def context(req: ContextRequest, _: Any = Depends(auth_dep)) -> JSONResponse:
        ctx = store.context(
            req.query,
            user_id=req.user_id,
            project_id=req.project_id,
            workspace_id=req.workspace_id,
            limit=req.limit,
            max_chars=req.max_chars,
            mode=req.mode,
        )
        return JSONResponse(ContextResponse(
            query=ctx.query, text=ctx.text,
            memory_count=ctx.memory_count, char_count=ctx.char_count,
            embedder_used=ctx.embedder_used, mode=ctx.mode,
            memories=ctx.memories,
        ).model_dump())

    @app.get("/v1/memory/{memory_id}")
    async def get_memory(memory_id: str, _: Any = Depends(auth_dep)) -> JSONResponse:
        item = store.get(memory_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        return JSONResponse(item.model_dump(mode="json"))

    @app.get("/v1/memory")
    async def list_memories(
        user_id: str | None = None,
        project_id: str | None = None,
        workspace_id: str | None = None,
        memory_type: str | None = None,
        limit: int = 20,
        _: Any = Depends(auth_dep),
    ) -> JSONResponse:
        kw: dict[str, Any] = {"limit": limit, "user_id": user_id, "project_id": project_id, "workspace_id": workspace_id}
        if memory_type:
            kw["memory_type"] = memory_type
        items = store.list(**kw)
        return JSONResponse({"memories": [i.model_dump(mode="json") for i in items]})

    @app.delete("/v1/memory/{memory_id}")
    async def delete_memory(memory_id: str, _: Any = Depends(auth_dep)) -> JSONResponse:
        deleted = store.delete(memory_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Memory not found")
        return JSONResponse({"deleted": True, "id": memory_id})

    @app.post("/v1/prompts")
    async def add_prompt(req: PromptRequest, _: Any = Depends(auth_dep)) -> JSONResponse:
        item = store.add_prompt(req.prompt, user_id=req.user_id, project_id=req.project_id)
        return JSONResponse({
            "id": item.id,
            "prompt_score": item.prompt_score,
            "risk_level": item.prompt_risk_level,
            "comments": item.prompt_comments,
            "suggestions": item.prompt_suggestions,
        })
