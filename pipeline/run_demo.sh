#!/bin/bash
# set -ex

streamlit run ./activities/local_demo.py --server.port 6006 -- $@

