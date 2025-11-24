from __future__ import annotations

from typing import Dict, List, Optional, Union

from model import Model


class SceneController:
    """Lightweight helper to manage models, shaders, and focus targets."""

    def __init__(self, renderer):
        self.renderer = renderer
        self._entries: List[Dict[str, object]] = []
        self._focus_index: int = -1

    # ------------------------------------------------------------------
    # Model registration and lookup
    # ------------------------------------------------------------------
    def add_model(
        self,
        model: Model,
        *,
        name: Optional[str] = None,
        shader_pair: Optional[tuple] = None,
        focus_distance: Optional[float] = None,
        reset_camera: bool = False,
    ) -> Model:
        if name:
            model.name = name

        if model not in self.renderer.scene:
            self.renderer.scene.append(model)

        entry = {
            "model": model,
            "focus_distance": focus_distance,
            "shader": None,
        }

        self._entries.append(entry)

        if shader_pair:
            vertex_src, fragment_src = shader_pair
            program = self.renderer.SetModelShaders(model, vertex_src, fragment_src)
            entry["shader"] = program

        if reset_camera or self._focus_index == -1:
            self.focus_index(len(self._entries) - 1, reset_angles=True)

        return model

    def remove_model(self, identifier: Union[str, int, Model]):
        model = self._resolve_model(identifier)
        if model is None:
            return

        self.renderer.scene = [obj for obj in self.renderer.scene if obj is not model]
        self._entries = [entry for entry in self._entries if entry["model"] is not model]

        if not self._entries:
            self._focus_index = -1
        else:
            self._focus_index %= len(self._entries)

    def get_models(self) -> List[Model]:
        return [entry["model"] for entry in self._entries]

    def get_model_names(self) -> List[str]:
        return [entry["model"].name for entry in self._entries]

    # ------------------------------------------------------------------
    # Focus handling
    # ------------------------------------------------------------------
    def focus_index(self, index: int, *, reset_angles: bool = False) -> Optional[Model]:
        if not self._entries:
            return None

        index %= len(self._entries)
        entry = self._entries[index]
        model: Model = entry["model"]  # type: ignore[assignment]
        focus_distance = entry.get("focus_distance")
        self.renderer.FocusOnModel(model, distance=focus_distance, reset_angles=reset_angles)
        self._focus_index = index
        return model

    def focus_next(self, *, reset_angles: bool = False) -> Optional[Model]:
        if not self._entries:
            return None
        next_index = (self._focus_index + 1) % len(self._entries)
        return self.focus_index(next_index, reset_angles=reset_angles)

    def focus_previous(self, *, reset_angles: bool = False) -> Optional[Model]:
        if not self._entries:
            return None
        prev_index = (self._focus_index - 1) % len(self._entries)
        return self.focus_index(prev_index, reset_angles=reset_angles)

    def get_focused_model(self) -> Optional[Model]:
        if self._focus_index == -1 or not self._entries:
            return None
        return self._entries[self._focus_index]["model"]  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Shader assignment helpers
    # ------------------------------------------------------------------
    def set_model_shaders(self, identifier: Union[str, int, Model], vertex_src, fragment_src):
        model = self._resolve_model(identifier)
        if model is None:
            raise ValueError("Model not found in controller")

        program = self.renderer.SetModelShaders(model, vertex_src, fragment_src)
        for entry in self._entries:
            if entry["model"] is model:
                entry["shader"] = program
                break
        return program

    def clear_model_shaders(self, identifier: Union[str, int, Model]):
        model = self._resolve_model(identifier)
        if model is None:
            return
        self.renderer.ClearModelShaders(model)
        for entry in self._entries:
            if entry["model"] is model:
                entry["shader"] = None
                break

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_model(self, identifier: Union[str, int, Model]) -> Optional[Model]:
        if isinstance(identifier, Model):
            return identifier if identifier in self.get_models() else None

        if isinstance(identifier, str):
            for entry in self._entries:
                model: Model = entry["model"]  # type: ignore[assignment]
                if model.name == identifier:
                    return model
            return None

        if isinstance(identifier, int):
            if not self._entries:
                return None
            index = identifier % len(self._entries)
            return self._entries[index]["model"]  # type: ignore[return-value]

        return None
