# Flujo Git seguro para Planificador Delivery Pro

Guia sencilla para trabajar sin romper la rama principal.

## 1. Comprobar la rama actual

```powershell
git branch --show-current
git status
```

Si estas en `main`, no hagas cambios directamente ahi.

## 2. Actualizar main

```powershell
git switch main
git pull
```

`git pull` trae los ultimos cambios publicados.

## 3. Crear una rama nueva

Usa un nombre claro:

```powershell
git switch -c feature/interfaz-moderna
git switch -c feature/editar-repartidores
git switch -c fix/descansos
```

Una rama sirve para aislar una tarea.

## 4. Revisar los cambios

```powershell
git status
git diff
```

`git status` muestra archivos cambiados.  
`git diff` muestra exactamente que lineas cambiaron.

## 5. Ejecutar comprobaciones

```powershell
python check_project.py
```

Si falla, corrige antes de guardar cambios.

## 6. Guardar un commit

```powershell
git add AGENTS.md check_project.py
git commit -m "Prepara flujo seguro de desarrollo"
```

Un commit es una foto local de tus cambios. No los sube a GitHub por si solo.

## 7. Volver a main

```powershell
git switch main
```

Si Git no te deja cambiar, revisa primero:

```powershell
git status
```

## 8. Fusionar una rama

Cuando la rama ya esta revisada:

```powershell
git switch main
git pull
git merge feature/editar-repartidores
```

`merge` integra los commits de una rama en otra.

## 9. Cancelar una rama que salio mal

Alternativa segura: vuelve a `main` y deja la rama apartada.

```powershell
git switch main
```

Si quieres borrar la rama local despues de confirmar que no sirve:

```powershell
git branch -d feature/interfaz-moderna
```

Si Git avisa de que la rama no esta fusionada, no fuerces el borrado salvo que estes seguro.

## 10. Volver al ultimo commit correcto

Primero mira que cambios tienes:

```powershell
git status
git diff
```

Alternativa segura: guarda los cambios temporalmente.

```powershell
git stash push -m "cambios antes de volver atras"
```

Despues puedes recuperarlos con:

```powershell
git stash pop
```

Evita `git reset --hard` salvo que entiendas que borra cambios locales no guardados. Antes de usarlo, crea una copia o pide ayuda.

## 11. Recuperar un archivo concreto

Para ver cambios en un archivo:

```powershell
git diff -- views/repartidores.py
```

Para descartar los cambios locales de un archivo concreto:

```powershell
git restore views/repartidores.py
```

Usalo solo si estas seguro de que quieres perder esos cambios de ese archivo.

## 12. Diferencia entre commit, push y merge

- `commit`: guarda cambios en tu repositorio local.
- `push`: sube commits a GitHub.
- `merge`: fusiona una rama dentro de otra.

## Flujo obligatorio para futuras tareas

1. Crear una rama.
2. Crear una copia de seguridad cuando se modifique la base de datos.
3. Implementar un unico cambio.
4. Anadir o actualizar pruebas.
5. Ejecutar `python check_project.py`.
6. Revisar `git diff`.
7. Mostrar al usuario los cambios.
8. Esperar autorizacion antes de hacer commit, push o merge.
