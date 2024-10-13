#!/bin/bash
cat text.txt | python add_errors.py > no_ecc.txt
cat text.txt | ../encode/hamming | python add_errors.py | ../decode/hamming > ecc.txt
