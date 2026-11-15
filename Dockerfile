# Build image for the ithalat wrist-rest generator - see Makefile.
# python:3.14-slim = Python 3.14 on Debian slim (pre-built wheels work, small
# footprint). Pinned to the minor on purpose, together with requirements.txt:
# a floating base image + unpinned wheels silently re-triangulate every
# published STL (same geometry, different bytes) on the next image rebuild.
# Every pinned wheel exists for linux/arm64 (Apple Silicon Docker) and
# linux/amd64 (GitHub Actions ubuntu-latest), so nothing compiles from source.
# The CPU architecture can still split a few faces along the other diagonal
# (under amd64 emulation: 3 triangles of ithalat-dock-usbc.stl, same vertices
# and volume), so an x86_64 rebuild of arm64-made STLs may differ in bytes only.
FROM python:3.14-slim

# Liberation Sans Bold: metric-compatible Arial substitute used for the
# "ithalat" engraving (matplotlib TextPath). Left unpinned on purpose (a hard
# apt pin breaks at the next Debian point release); a changed font only
# re-triangulates the engraving.
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-liberation \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --root-user-action=ignore -r /tmp/requirements.txt

# The Makefile runs the container as the caller's uid:gid (501 on a Mac, 1001 on
# GitHub's runners), which has no passwd entry and so no writable home.
# matplotlib wants a writable config dir and any other cache goes under HOME;
# /tmp works for any --user.
ENV MPLCONFIGDIR=/tmp/mpl \
    HOME=/tmp
WORKDIR /app
