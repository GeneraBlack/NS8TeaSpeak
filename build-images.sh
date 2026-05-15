#!/bin/bash

#
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

# Terminate on error
set -e

# Prepare variables for later use
images=()
# The image will be pushed to GitHub container registry
repobase="${REPOBASE:-ghcr.io/nethserver}"
# Configure image names
reponame="teaspeak"
servicename="${reponame}-service"
webservicename="${reponame}-web"
imagetag="${IMAGETAG:-latest}"
uinodeimage="docker.io/library/node:16.20.2-bullseye-slim"
uibuilder="nodebuilder-${reponame}-node16"

# Reuse existing nodebuilder container, to speed up builds
if ! buildah containers --format "{{.ContainerName}}" | grep -q "^${uibuilder}$"; then
    echo "Pulling NodeJS runtime..."
    buildah from --name "${uibuilder}" -v "${PWD}:/usr/src:Z" "${uinodeimage}"
fi

# Create a new empty container image
container=$(buildah from scratch)

echo "Build static UI files with node..."
buildah run \
    --workingdir=/usr/src/ui \
    "${uibuilder}" \
    sh -c "yarn install && yarn build"

echo "Build TeaSpeak service image..."
buildah bud \
    --tag "${repobase}/${servicename}" \
    --build-arg "TEASPEAK_VERSION=${TEASPEAK_VERSION:-1.5.6}" \
    images/teaspeak-service

echo "Build TeaWeb image..."
buildah bud \
    --tag "${repobase}/${webservicename}" \
    --build-arg "TEAWEB_VERSION=${TEAWEB_VERSION:-59737567}" \
    images/teaspeak-web

# Add imageroot directory to the container image
buildah add "${container}" imageroot /imageroot
buildah add "${container}" ui/dist /ui

# Setup the entrypoint, grant firewall management, declare the service image and set a rootless container
buildah config --entrypoint=/ \
    --label="org.nethserver.authorizations=node:fwadm traefik@node:routeadm" \
    --label="org.nethserver.rootfull=0" \
    --label="org.nethserver.max-per-node=1" \
    --label="org.nethserver.tcp-ports-demand=1" \
    --label="org.nethserver.images=${repobase}/${servicename}:${imagetag} ${repobase}/${webservicename}:${imagetag}" \
    --label="org.nethserver.volumes=database files logs crashdumps certs" \
    "${container}"

# Commit the image
buildah commit "${container}" "${repobase}/${reponame}"

# Append the image URL to the images array
images+=("${repobase}/${servicename}" "${repobase}/${webservicename}" "${repobase}/${reponame}")

#
# NOTICE:
#
# It is possible to build and publish multiple images.
#
# 1. create another buildah container
# 2. add things to it and commit it
# 3. append the image url to the images array
#

#
# Setup CI when pushing to Github. 
# Warning! docker::// protocol expects lowercase letters (,,)
if [[ -n "${CI}" ]]; then
    # Set output value for Github Actions
    printf "images=%s\n" "${images[*],,}" >> "${GITHUB_OUTPUT}"
else
    # Just print info for manual push
    printf "Publish the images with:\n\n"
    for image in "${images[@],,}"; do printf "  buildah push %s docker://%s:%s\n" "${image}" "${image}" "${IMAGETAG:-latest}" ; done
    printf "\n"
fi
