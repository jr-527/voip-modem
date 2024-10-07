#!/bin/bash
cat text.txt | python add_errors.py > no_ecc.txt
cat text.txt | ../encode/test | python add_errors.py | ../decode/test > ecc.txt
