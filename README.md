# Proyecto 3

## Ejecución
Para ejecutar el renderizador, corre el archivo `RendererOpenGL2025.py`.

## Controles
- **Foco de modelos**: `M` / `N` para recorrer modelos registrados.
- **Shaders del modelo enfocado**: `0` restablece; `1` Checker, `2` Fresnel, `3` Scanlines, `5` Unlit; `6` Básico, `7` Twist, `8` Pulse, `9` Ripple; `4` aplica Decal; `P` alterna el preset global.
- **Cámara orbital**: arrastra con el mouse; rueda o `A`/`D` zoom; flechas o `W`/`S` elevación; `C` alterna modo libre.
- **Cámara libre**: `W`/`S` pitch, `A`/`D` yaw, `Q`/`E` roll; flechas y `WASD` desplazan.
- **Iluminación**: `T/G`, `F/H`, `R/Y` mueven la luz puntual en los ejes Z, X, Y.
- **Parámetros de shader**: `Z` / `X` ajustan el valor del shader para el modelo enfocado.
- **Post-procesos**: `V` activa la máscara del logo; `B` alterna el decal global.
- **Salir**: `ESC`.

## Referencia
![Referencia](assets/Referencia.avif)

## Resultado
<video width="100%" controls autoplay>
  <source src="Resultado.mp4" type="video/mp4">
</video>