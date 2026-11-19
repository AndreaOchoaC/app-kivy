#!/usr/bin/env bash
# Publica archivos (APK / IPA) en la «release» de la rama: una release por rama, que se
# actualiza en cada build. Uso:   publish_release.sh <slug_de_la_rama> <archivo> [<archivo> ...]
#
# Necesita GH_TOKEN (lo da el workflow) y las variables normales de GitHub Actions.
# Android e iOS usan la MISMA release, así que aquí se maneja que ambos lleguen casi a la vez.
set -euo pipefail

slug="$1"
shift
tag="build-${slug}"
branch="${GITHUB_REF_NAME:-$slug}"
short_sha="${GITHUB_SHA:0:7}"
repo="${GITHUB_REPOSITORY}"
export GH_REPO="$repo"

if [ "$branch" = "main" ]; then
  title="Versión principal (main)"
else
  title="Build de la rama ${branch}"
fi

notes="Última compilación automática de la rama \`${branch}\`.

| | |
|---|---|
| Commit | \`${short_sha}\` |
| Fecha | $(date -u +'%Y-%m-%d %H:%M UTC') |

**Android:** descarga el \`.apk\` en el celular y ábrelo. **iPhone:** descarga el \`.ipa\` y fírmalo con Sideloadly.
Instrucciones completas: [docs/BUILDS.md](https://github.com/${repo}/blob/main/docs/BUILDS.md)"

# Crear la release si no existe. Si otro workflow (Android/iOS) la crea en este instante,
# el segundo «create» falla y simplemente seguimos.
if ! gh release view "$tag" >/dev/null 2>&1; then
  gh release create "$tag" --target "$GITHUB_SHA" --title "$title" --notes "$notes" --prerelease \
    || gh release view "$tag" >/dev/null
fi

gh release upload "$tag" "$@" --clobber
gh release edit "$tag" --title "$title" --notes "$notes" --prerelease

# Mueve la etiqueta al commit actual para que la release apunte al código que se compiló.
gh api --method PATCH "repos/${repo}/git/refs/tags/${tag}" -f sha="$GITHUB_SHA" -F force=true >/dev/null \
  || echo "No se pudo mover la etiqueta (no es grave)."

echo "Publicado en: https://github.com/${repo}/releases/tag/${tag}"
