#!/usr/bin/env python3
"""
Generate coverage badges from gcovr output.

This script parses gcovr HTML or JSON output and generates SVG badges
in shields.io flat style for lines, functions, and branches coverage.
"""

import json
import os
import re
import sys
from pathlib import Path


# C++ Alliance logo (SVG, base64-encoded)
LOGO_BASE64 = (
    "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz4KPCEtLSBHZW5lcmF0b3I6IEFk"
    "b2JlIElsbHVzdHJhdG9yIDI0LjAuMywgU1ZHIEV4cG9ydCBQbHVnLUluIC4gU1ZHIFZlcnNpb246"
    "IDYuMDAgQnVpbGQgMCkgIC0tPgo8c3ZnIHZlcnNpb249IjEuMSIgd2lkdGg9IjQxNSIgaGVpZ2h0"
    "PSIzODAiIGlkPSJMYXllcl8xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHht"
    "bG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB4PSIwcHgiIHk9IjBweCIK"
    "CSB2aWV3Qm94PSIxOTAgMTIwIDQxNSAzODAiIHhtbDpzcGFjZT0icHJlc2VydmUiPgo8c3R5bGUg"
    "dHlwZT0idGV4dC9jc3MiPgoJLnN0MHtmaWxsLXJ1bGU6ZXZlbm9kZDtjbGlwLXJ1bGU6ZXZlbm9k"
    "ZDtmaWxsOiNBOTFDMjE7fQoJLnN0MXtmaWxsLXJ1bGU6ZXZlbm9kZDtjbGlwLXJ1bGU6ZXZlbm9k"
    "ZDtmaWxsOiNGRkZGRkY7fQoJLnN0MntmaWxsOiNGRkZGRkY7fQo8L3N0eWxlPgo8Zz4KCTxnPgoJ"
    "CTxnPgoJCQk8cGF0aCBjbGFzcz0ic3QwIiBkPSJNMjY2LjE1LDE3NS4yN2MtOS40NCwwLjU4LTE2"
    "LjE0LDIuMTktMjAuMDgsNC43OWMtNC40LDIuOTQtNi4zOCw3Ljc4LTUuODcsMTQuNTkKCQkJCWMw"
    "LjE5LDIuNTEsMC43OSw1Ljk4LDEuODYsMTAuNDFsMy42NCwxNS43YzEuMjgsNS4yNywyLjAzLDku"
    "NjYsMi4yOSwxMy4xNGMxLjIsMTYuMjgtNS40NSwyNy4wOS0xOS45MywzMi40NAoJCQkJYzE1LjIs"
    "NC40LDIzLjQyLDE0Ljg2LDI0LjY0LDMxLjM0YzAuMjUsMy40LDAuMTgsNy42Ny0wLjI2LDEyLjg0"
    "bC0xLjQsMTUuNzVjLTAuNCw0LjU1LTAuNTMsOC4wOC0wLjM1LDEwLjU2CgkJCQljMC41LDYuODEs"
    "My4xOCwxMS41Miw3Ljk5LDE0LjExYzQuNzksMi41OCwxMC4zMSwzLjYyLDIxLjUxLDMuMzNjMC4w"
    "NCwwLDAuMS0wLjA0LDAuMTIsMGMzLjIsNS42Myw3LjE5LDExLjE1LDEyLjcyLDE2LjQKCQkJCWwt"
    "MTIuMzksMC40MmMtMTUuNDEsMC41My0yNy40Ny0xLjg1LTM2LjA5LTcuMThjLTguNjItNS4yOS0x"
    "My4zMi0xMy4yMy0xNC4xLTIzLjgzYy0wLjMzLTQuNTItMC4xNy05LjY1LDAuNDYtMTUuMzdsMi4z"
    "OS0yMC4yOAoJCQkJYzAuMzItMy4wNCwwLjM3LTYuMDYsMC4xNS05Yy0xLjAyLTEzLjg4LTEwLjAy"
    "LTIwLjU2LTI2Ljk4LTE5Ljk4bC0xMC4zNCwwLjM1bC0xLjIzLTE2LjcxbDEwLjM0LTAuMzUKCQkJ"
    "CWMxNi45Ni0wLjU4LDI0LjkzLTcuNzksMjMuOTEtMjEuNjRjLTAuMjItMi45NC0wLjcxLTUuOTEt"
    "MS40OC04Ljk0bC01LjM2LTIwLjA2Yy0xLjQ3LTUuNjUtMi4zOC0xMC43NC0yLjcyLTE1LjI2CgkJ"
    "CQljLTEuNjEtMjEuNzcsMTMuNS0zMy4yNCw0NS4zOC0zNC4zMWwwLjYtMC4wMkwyNjYuMTUsMTc1"
    "LjI3eiIvPgoJCTwvZz4KCQk8Zz4KCQkJPHBhdGggY2xhc3M9InN0MCIgZD0iTTUyNS42LDE3NS4y"
    "N2M5LjQ0LDAuNTgsMTYuMTQsMi4xOSwyMC4wOCw0Ljc5YzQuNCwyLjk0LDYuMzgsNy43OCw1Ljg3"
    "LDE0LjU5CgkJCQljLTAuMTksMi41MS0wLjc5LDUuOTgtMS44NiwxMC40MWwtMy42NCwxNS43Yy0x"
    "LjI4LDUuMjctMi4wMyw5LjY2LTIuMjksMTMuMTRjLTEuMiwxNi4yOCw1LjQ2LDI3LjA5LDE5Ljkz"
    "LDMyLjQ0CgkJCQljLTE1LjIsNC40LTIzLjQyLDE0Ljg2LTI0LjY0LDMxLjM0Yy0wLjI1LDMuNC0w"
    "LjE4LDcuNjcsMC4yNiwxMi44NGwxLjQsMTUuNzVjMC40LDQuNTUsMC41Myw4LjA4LDAuMzUsMTAu"
    "NTYKCQkJCWMtMC41LDYuODEtMy4xOCwxMS41Mi03Ljk5LDE0LjExYy00Ljc5LDIuNTgtMTAuMzEs"
    "My42Mi0yMS41MSwzLjMzYy0wLjA0LDAtMC4xLTAuMDQtMC4xMiwwYy0zLjIsNS42My03LjIsMTEu"
    "MTUtMTIuNzIsMTYuNAoJCQkJbDEyLjM5LDAuNDJjMTUuNDEsMC41MywyNy40Ny0xLjg1LDM2LjA5"
    "LTcuMThjOC42Mi01LjI5LDEzLjMyLTEzLjIzLDE0LjExLTIzLjgzYzAuMzMtNC41MiwwLjE3LTku"
    "NjUtMC40Ni0xNS4zN2wtMi4zOS0yMC4yOAoJCQkJYy0wLjMyLTMuMDQtMC4zNy02LjA2LTAuMTUt"
    "OWMxLjAzLTEzLjg4LDEwLjAyLTIwLjU2LDI2Ljk4LTE5Ljk4bDEwLjM0LDAuMzVsMS4yMy0xNi43"
    "MWwtMTAuMzQtMC4zNQoJCQkJYy0xNi45Ni0wLjU4LTI0LjkzLTcuNzktMjMuOTEtMjEuNjRjMC4y"
    "Mi0yLjk0LDAuNzEtNS45MSwxLjQ4LTguOTRsNS4zNi0yMC4wNmMxLjQ3LTUuNjUsMi4zOC0xMC43"
    "NCwyLjcyLTE1LjI2CgkJCQljMS42MS0yMS43Ny0xMy41LTMzLjI0LTQ1LjM4LTM0LjMxbC0wLjYt"
    "MC4wMkw1MjUuNiwxNzUuMjd6Ii8+CgkJPC9nPgoJCTxnPgoJCQk8cGF0aCBjbGFzcz0ic3QwIiBk"
    "PSJNMzI3LjYsNDExLjI3Yy0xMC44Myw0LjctMzguMDcsMi4zLTQ3Ljk5LTAuNDVsLTAuMDgsMC4y"
    "YzE0LjU2LDQuOTUsMzAuNDksOS4wMyw0NS42MSwxMgoJCQkJQzMyNS4yOCw0MjIuNTUsMzI3LjA5"
    "LDQxMS40OCwzMjcuNiw0MTEuMjd6Ii8+CgkJPC9nPgoJCTxnPgoJCQk8cGF0aCBjbGFzcz0ic3Qw"
    "IiBkPSJNNDY0LjQsNDExLjI3YzEwLjgzLDQuNywzOC4wNywyLjMsNDcuOTktMC40NWwwLjA4LDAu"
    "MmMtMTQuNTYsNC45NS0zMC40OSw5LjAzLTQ1LjYxLDEyCgkJCQlDNDY2LjcyLDQyMi41NSw0NjQu"
    "OTEsNDExLjQ4LDQ2NC40LDQxMS4yN3oiLz4KCQk8L2c+CgkJPGc+CgkJCTxwYXRoIGNsYXNzPSJz"
    "dDAiIGQ9Ik01MTMuMiw0MTUuMDFjLTc2LjU1LDI4LjQ2LTE1Ny44NSwyOC40NS0yMzQuNCwwbC0x"
    "NS42Myw0NS42OGM0MS4zMywxMy43OSw4Mi43NiwyMi44NiwxMzIuODMsMjIuODYKCQkJCXM5MS41"
    "Ni05LjEyLDEzMi44OS0yMi44Nkw1MTMuMiw0MTUuMDF6Ii8+CgkJPC9nPgoJCTxnPgoJCQk8cGF0"
    "aCBjbGFzcz0ic3QwIiBkPSJNNTg1LjU4LDM2MC43MWMtMzYuOTEsMjItNzcuMDQsMzcuNzMtMTE5"
    "LjkyLDQ2LjE3bC0yLjA5LDAuNGMwLjM1LDEuNiwyNS4zMiw1LjY0LDUyLjItMS40OWwxMy40OSwz"
    "NS40NQoJCQkJYzIyLjkyLTYuNTMsNDkuMjgtMTYuMjUsNzIuMjMtMjkuODhjLTAuOSwwLjUzLTQw"
    "LjEzLTkuNTQtNDAuMTMtOS41NEw1ODUuNTgsMzYwLjcxeiIvPgoJCTwvZz4KCQk8Zz4KCQkJPHBh"
    "dGggY2xhc3M9InN0MCIgZD0iTTIwNi40MiwzNjAuNzFjMzYuOTEsMjIsNzcuMDQsMzcuNzMsMTE5"
    "LjkyLDQ2LjE3bDIuMDksMC40Yy0wLjM1LDEuNi0yNS4zMiw1LjY0LTUyLjItMS40OWwtMTMuNDks"
    "MzUuNDUKCQkJCWMtMjIuOTItNi41My00OS4yOC0xNi4yNS03Mi4yMy0yOS44OGMwLjksMC41Myw0"
    "MC4xMy05LjU0LDQwLjEzLTkuNTRMMjA2LjQyLDM2MC43MXoiLz4KCQk8L2c+CgkJPGc+CgkJCTxn"
    "PgoJCQkJPHBhdGggY2xhc3M9InN0MCIgZD0iTTM5Ni4xOCwxMjguNDVIMzk2Yy02Ny45NCwwLTEy"
    "My4xNSwxMS41OS0xMjMuNTcsMTguMzdsNC4wNSwxNjMuNThjMCw3MC42LDc5LjU3LDgzLjkzLDEx"
    "OS42MSwxMTQuODYKCQkJCQlDNDM2LjEzLDM5NC4zMyw1MTUuNywzODEsNTE1LjcsMzEwLjRsNC4w"
    "NS0xNjMuNThDNTE5LjMzLDE0MC4wNCw0NjQuMTIsMTI4LjQ1LDM5Ni4xOCwxMjguNDV6Ii8+CgkJ"
    "CQk8cGF0aCBjbGFzcz0ic3QwIiBkPSJNNTAyLjE3LDMxMC4zNWMtMy43NCw1OC4xNC03Mi41OCw2"
    "OS45LTEwNi4wOCw5Ni41Yy0zMy41LTI2LjYtMTAyLjM0LTM4LjM2LTEwNi4wOC05Ni41bC0yLjAy"
    "LTE1My45OQoJCQkJCWMwLjI4LTYuNDcsNjkuMDgtMTQuNTYsMTA4LjEtMTQuNTZjMzkuNTcsMCwx"
    "MDcuODIsOC4wOSwxMDguMSwxNC41Nkw1MDIuMTcsMzEwLjM1eiIvPgoJCQk8L2c+CgkJCTxwYXRo"
    "IGNsYXNzPSJzdDEiIGQ9Ik0zOTYuMDksMTQxLjhjLTM5LjAyLDAtMTA3LjgyLDguMDktMTA4LjEs"
    "MTQuNTZsMi4wMiwxNTMuOTljMy43NCw1OC4xNCw3Mi41OCw2OS45LDEwNi4wOCw5Ni41CgkJCQlj"
    "MzMuNS0yNi42LDEwMi4zNC0zOC4zNiwxMDYuMDgtOTYuNWwyLjAyLTE1My45OUM1MDMuOTEsMTQ5"
    "Ljg5LDQzNS42NiwxNDEuOCwzOTYuMDksMTQxLjh6IE00ODguNjMsMzA2LjgxCgkJCQljLTMuMjYs"
    "NTAuNy02My4zMSw2MC45Ni05Mi41NCw4NC4xNmMtMjkuMjMtMjMuMi04OS4yNy0zMy40Ni05Mi41"
    "NC04NC4xNmwtMS43Ni0xMzguMTNjMC4yNC01LjY1LDYwLjI2LTEyLjcxLDk0LjMtMTIuNzEKCQkJ"
    "CWMzNC41MiwwLDk0LjA1LDcuMDYsOTQuMywxMi43MUw0ODguNjMsMzA2LjgxeiIvPgoJCTwvZz4K"
    "CQk8Zz4KCQkJPHBhdGggY2xhc3M9InN0MCIgZD0iTTQ5MC4zOSwxNjguNjhsLTEuNzYsMTM4LjEz"
    "Yy0zLjI2LDUwLjctNjMuMzEsNjAuOTYtOTIuNTQsODQuMTZjLTI5LjIzLTIzLjItODkuMjctMzMu"
    "NDYtOTIuNTQtODQuMTYKCQkJCWwtMS43Ni0xMzguMTNjMC4yNC01LjY1LDYwLjI2LTEyLjcxLDk0"
    "LjMtMTIuNzFDNDMwLjYxLDE1NS45Nyw0OTAuMTQsMTYzLjA0LDQ5MC4zOSwxNjguNjh6Ii8+CgkJ"
    "PC9nPgoJCTxnPgoJCQk8cG9seWdvbiBjbGFzcz0ic3QxIiBwb2ludHM9IjM4Ny42OCwyMzcuMTcg"
    "Mzk4LjE2LDIzNy4xNyAzOTguMTYsMjU4LjEzIDQxOS4xMiwyNTguMTMgNDE5LjEyLDI2OC42MSAz"
    "OTguMTYsMjY4LjYxIAoJCQkJMzk4LjE2LDI4OS41NyAzODcuNjgsMjg5LjU3IDM4Ny42OCwyNjgu"
    "NjEgMzY2LjcyLDI2OC42MSAzNjYuNzIsMjU4LjEzIDM4Ny42OCwyNTguMTMgCQkJIi8+CgkJPC9n"
    "PgoJCTxnPgoJCQk8cG9seWdvbiBjbGFzcz0ic3QxIiBwb2ludHM9IjQ1MC4xNiwyMzcuMTcgNDYw"
    "LjY0LDIzNy4xNyA0NjAuNjQsMjU4LjEzIDQ4MS42LDI1OC4xMyA0ODEuNiwyNjguNjEgNDYwLjY0"
    "LDI2OC42MSA0NjAuNjQsMjg5LjU3IAoJCQkJNDUwLjE2LDI4OS41NyA0NTAuMTYsMjY4LjYxIDQy"
    "OS4yLDI2OC42MSA0MjkuMiwyNTguMTMgNDUwLjE2LDI1OC4xMyAJCQkiLz4KCQk8L2c+Cgk8L2c+"
    "Cgk8Zz4KCQk8Zz4KCQkJPHBhdGggY2xhc3M9InN0MiIgZD0iTTMwMy4xLDQ1NS4yMmMtNC41MS0x"
    "LjE2LTYuNzYtMS43Ny0xMS4yNC0zLjA0Yy0xLjQ1LDEuOC0yLjE5LDIuNy0zLjY2LDQuNDgKCQkJ"
    "CWMtMi4zMi0wLjY3LTMuNDctMS4wMi01Ljc4LTEuNzJjNy4zNC04LjE1LDEwLjg4LTEyLjI5LDE3"
    "LjY4LTIwLjcxYzIuMDksMC41OCwzLjE0LDAuODcsNS4yNCwxLjQyCgkJCQljMS41NCwxMC42OCwy"
    "LjQ2LDE2LjAzLDQuNjIsMjYuNzNjLTIuNC0wLjU2LTMuNi0wLjg1LTYtMS40NUMzMDMuNiw0NTgu"
    "NjQsMzAzLjQzLDQ1Ny41LDMwMy4xLDQ1NS4yMnogTTMwMi40NSw0NTAuNTQKCQkJCWMtMC41NS00"
    "LjA3LTAuOC02LjExLTEuMjctMTAuMTdjLTIuNDksMy4yNy0zLjc1LDQuODktNi4zMiw4LjEyQzI5"
    "Ny44OSw0NDkuMzQsMjk5LjQxLDQ0OS43NSwzMDIuNDUsNDUwLjU0eiIvPgoJCQk8cGF0aCBjbGFz"
    "cz0ic3QyIiBkPSJNMzIzLjE5LDQzOS45MWMyLjE1LDAuNDYsMy4yMiwwLjY4LDUuMzcsMS4xYy0x"
    "LjU0LDcuOS0yLjMyLDExLjg1LTMuODYsMTkuNzYKCQkJCWM0LjkzLDAuOTcsNy40LDEuNDEsMTIu"
    "MzUsMi4yMWMtMC4zLDEuODUtMC40NCwyLjc3LTAuNzQsNC42MmMtNy4zMi0xLjE3LTEwLjk4LTEu"
    "ODYtMTguMjYtMy40MQoJCQkJQzMyMC4xMSw0NTQuNDcsMzIxLjE0LDQ0OS42MiwzMjMuMTksNDM5"
    "LjkxeiIvPgoJCQk8cGF0aCBjbGFzcz0ic3QyIiBkPSJNMzQ4LjEzLDQ0NC4yN2MyLjE2LDAuMjks"
    "My4yNCwwLjQzLDUuNDEsMC42OGMtMC45Niw3Ljk5LTEuNDUsMTEuOTktMi40MSwxOS45OAoJCQkJ"
    "YzQuOTYsMC41OCw3LjQ0LDAuODIsMTIuNCwxLjIzYy0wLjE2LDEuODYtMC4yNCwyLjgtMC40LDQu"
    "NjZjLTcuMzUtMC42LTExLjAyLTAuOTgtMTguMzYtMS45OAoJCQkJQzM0Ni4xMSw0NTkuMDEsMzQ2"
    "Ljc5LDQ1NC4xLDM0OC4xMyw0NDQuMjd6Ii8+CgkJCTxwYXRoIGNsYXNzPSJzdDIiIGQ9Ik0zNzMu"
    "MTcsNDQ2LjY4YzIuMTcsMC4xMywzLjI1LDAuMTksNS40MiwwLjI5Yy0wLjQ3LDkuOTEtMC43LDE0"
    "Ljg2LTEuMTcsMjQuNzYKCQkJCWMtMi4zMy0wLjEtMy40OS0wLjE3LTUuODEtMC4zMUMzNzIuMjQs"
    "NDYxLjUzLDM3Mi41NSw0NTYuNTgsMzczLjE3LDQ0Ni42OHoiLz4KCQkJPHBhdGggY2xhc3M9InN0"
    "MiIgZD0iTTQwNS4zMSw0NjYuNjdjLTQuNiwwLjEyLTYuOSwwLjE1LTExLjUxLDAuMTRjLTAuODgs"
    "Mi4xMi0xLjMzLDMuMTgtMi4yNCw1LjNjLTIuMzktMC4wMi0zLjU4LTAuMDQtNS45Ni0wLjEKCQkJ"
    "CWM0LjczLTkuODEsNi45NS0xNC43NSwxMS4wOC0yNC42OGMyLjE1LTAuMDEsMy4yMi0wLjAyLDUu"
    "MzYtMC4wN2M0LjQsOS44Myw2Ljc1LDE0LjcyLDExLjc1LDI0LjRjLTIuNDQsMC4xMi0zLjY2LDAu"
    "MTctNi4xLDAuMjUKCQkJCUM0MDYuNzIsNDY5LjgyLDQwNi4yNSw0NjguNzcsNDA1LjMxLDQ2Ni42"
    "N3ogTTQwMy40LDQ2Mi4zNmMtMS42NC0zLjc2LTIuNDQtNS42NS00LTkuNDJjLTEuNDYsMy44MS0y"
    "LjIyLDUuNzItMy43Niw5LjUyCgkJCQlDMzk4Ljc0LDQ2Mi40NSw0MDAuMyw0NjIuNDMsNDAzLjQs"
    "NDYyLjM2eiIvPgoJCQk8cGF0aCBjbGFzcz0ic3QyIiBkPSJNNDQxLjYxLDQ0NC4zMWMxLjM0LDku"
    "ODMsMi4wMSwxNC43NCwzLjM1LDI0LjU3Yy0xLjksMC4yNS0yLjg1LDAuMzYtNC43NSwwLjU5CgkJ"
    "CQljLTUuNzItNS4zOS04LjQ5LTguMTQtMTMuODItMTMuNzNjMC41Myw2LDAuOCw5LDEuMzMsMTVj"
    "LTIuMjksMC4xOS0zLjQ0LDAuMjgtNS43MywwLjQ0Yy0wLjczLTkuODktMS4wOS0xNC44NC0xLjgx"
    "LTI0LjczCgkJCQljMS43OS0wLjEzLDIuNjktMC4xOSw0LjQ4LTAuMzRjNS4xNyw1LjYyLDcuODYs"
    "OC4zOCwxMy40MiwxMy44Yy0wLjcyLTUuOTgtMS4wOC04Ljk3LTEuOC0xNC45NQoJCQkJQzQzOC40"
    "Miw0NDQuNzIsNDM5LjQ4LDQ0NC41OSw0NDEuNjEsNDQ0LjMxeiIvPgoJCQk8cGF0aCBjbGFzcz0i"
    "c3QyIiBkPSJNNDUyLjc5LDQ1NS4yNGMtMS4yMS03LjM4LDMuMy0xMy40NiwxMC41LTE0Ljg1YzMu"
    "OTktMC43Nyw3LjY0LDAuMDUsMTAuNDcsMi4zMgoJCQkJYy0xLjA4LDEuNjMtMS42MiwyLjQ1LTIu"
    "NzMsNC4wN2MtMS45OS0xLjU0LTQuMTctMi4xLTYuNTEtMS42NWMtNC4zOCwwLjg1LTYuOTMsNC41"
    "OC02LjEsOS4xOGMwLjgzLDQuNiw0LjY3LDcuMjcsOS4yNiw2LjM4CgkJCQljMi40NS0wLjQ3LDQu"
    "MzEtMS44Nyw1LjUxLTQuMTFjMS43MywxLjAzLDIuNjEsMS41Myw0LjM2LDIuNTRjLTEuNjUsMy4z"
    "MS00LjksNS42LTkuMjIsNi40MwoJCQkJQzQ2MC42NCw0NjcuMDMsNDU0LDQ2Mi42Miw0NTIuNzks"
    "NDU1LjI0eiIvPgoJCQk8cGF0aCBjbGFzcz0ic3QyIiBkPSJNNTA0Ljk3LDQ1MS4zN2MwLjU1LDEu"
    "NzYsMC44MywyLjY0LDEuMzksNC40Yy03LjUzLDIuMjYtMTEuMzIsMy4yOS0xOC45Myw1LjE2CgkJ"
    "CQljLTIuNDgtOS42Mi0zLjcyLTE0LjQyLTYuMi0yNC4wNGM2LjkzLTEuNywxMC4zOC0yLjY0LDE3"
    "LjI0LTQuNjljMC41NSwxLjc2LDAuODMsMi42NCwxLjM4LDQuNGMtNC44MywxLjQ0LTcuMjYsMi4x"
    "Mi0xMi4xMywzLjQKCQkJCWMwLjU3LDIuMDgsMC44NiwzLjEyLDEuNDMsNS4yYzQuMzctMS4xNCw2"
    "LjU1LTEuNzUsMTAuODgtMy4wM2MwLjUzLDEuNzEsMC43OSwyLjU2LDEuMzIsNC4yN2MtNC4zOSwx"
    "LjI5LTYuNiwxLjkxLTExLjAyLDMuMDYKCQkJCWMwLjYxLDIuMjIsMC45MSwzLjMyLDEuNTIsNS41"
    "NEM0OTcuMTIsNDUzLjY4LDQ5OS43NCw0NTIuOTQsNTA0Ljk3LDQ1MS4zN3oiLz4KCQk8L2c+Cgk8"
    "L2c+Cgk8Zz4KCQk8cGF0aCBjbGFzcz0ic3QyIiBkPSJNNDQyLjk5LDIwNi4zMWMwLjI5LTYuNjUs"
    "MS40NS0xMC4zNCwwLjQzLTExLjM3Yy0xLjAxLTEuMDMtMi4zMS0xLjMzLTcuMjMtMS43NwoJCQlj"
    "LTQuOTEtMC40NC0xOS4yMi00LjczLTQ0LjgtNC4xNGMtMjUuNTgsMC41OS01NS4wNiw5LjQ1LTY5"
    "Ljk1LDQ0LjkxczIuNjYsNzYuODQsMzEuMTQsOTEuNDRjMjguNTQsMTQuNjIsNjMuMTQsMTEuNDYs"
    "ODAuNTcsNy41MwoJCQljMi44My0wLjY0LDUuMTMtMi4xOSw2LjY1LTYuMDZjMy4wNS03Ljc4LDMu"
    "NjctMTcuNjksNC4wNS0yMS44MmMwLjQzLTQuNzMtMy4wMy0zLjI1LTQuMDUtMS40OHMtMS40OSw4"
    "LjI5LTkuMSwxNC40MwoJCQljLTEzLjAxLDEwLjQ5LTM5LjUzLDExLjg4LTU3LjY2LTAuNTljLTIz"
    "LjQxLTE2LjEtMzQuNjgtNDAuNjItMjkuMDUtNzYuNTJjNS42NC0zNS45LDMxLjY1LTQyLjQsNDcu"
    "NjktNDIuMjUKCQkJYzE2LjA0LDAuMTUsMzYuMjUsMi41MSw0My45MywxOC4wMmMxLjc3LDMuNTgs"
    "Mi4xOSw2LjMsMi4zMSw4Ljk3YzAuMTQsMy4yLDMuMjgsMy4zMywzLjksMC44OQoJCQlDNDQyLjU5"
    "LDIyMy41Niw0NDIuOTksMjA2LjMxLDQ0Mi45OSwyMDYuMzF6Ii8+Cgk8L2c+CjwvZz4KPC9zdmc+"
    "Cg=="
)
LOGO_MIME = "image/svg+xml"
LOGO_WIDTH = 14
LOGO_PAD_LEFT = 3   # padding before logo
LOGO_PAD_RIGHT = 0  # padding after logo (text has its own internal padding)

# Shields.io flat-style SVG badge template with logo
BADGE_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="20" role="img" aria-label="{label}: {value}%">
  <title>{label}: {value}%</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <image x="{logo_x}" y="3" width="14" height="14" xlink:href="data:image/svg+xml;base64,{logo_base64}"/>
    <text aria-hidden="true" x="{label_x}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)">{label}</text>
    <text x="{label_x}" y="140" transform="scale(.1)" fill="#fff">{label}</text>
    <text aria-hidden="true" x="{value_x}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)">{value}%</text>
    <text x="{value_x}" y="140" transform="scale(.1)" fill="#fff">{value}%</text>
  </g>
</svg>'''


# Standard shields.io colors
COLORS = {
    'brightgreen': '#4c1',
    'green': '#97ca00',
    'yellowgreen': '#a4a61d',
    'yellow': '#dfb317',
    'orange': '#fe7d37',
    'red': '#e05d44',
}


def get_color_for_coverage(percentage):
    """Return shields.io color based on coverage percentage."""
    try:
        pct = float(percentage)
        if pct >= 90:
            return COLORS['brightgreen']
        elif pct >= 75:
            return COLORS['yellow']
        else:
            return COLORS['red']
    except (ValueError, TypeError):
        return COLORS['red']


def estimate_text_width(text):
    """Estimate text width in pixels (approximate)."""
    # Average character width for Verdana 11px is about 6.5-7px
    return len(text) * 7 + 10


def generate_badge_svg(label, value):
    """Generate an SVG badge with the given label and value."""
    value_str = f"{value:.0f}" if isinstance(value, float) else str(value)

    logo_space = LOGO_PAD_LEFT + LOGO_WIDTH + LOGO_PAD_RIGHT
    text_width = estimate_text_width(label)
    label_width = logo_space + text_width
    value_width = estimate_text_width(f"{value_str}%")
    total_width = label_width + value_width

    color = get_color_for_coverage(value)

    # Logo sits at left edge with padding
    logo_x = LOGO_PAD_LEFT
    # Label text is centered in the remaining space after the logo
    label_x = (logo_space + text_width / 2) * 10
    # Value text is centered in the value section
    value_x = (label_width + value_width / 2) * 10

    return BADGE_TEMPLATE.format(
        width=total_width,
        label_width=label_width,
        value_width=value_width,
        label=label,
        value=value_str,
        color=color,
        logo_x=logo_x,
        logo_base64=LOGO_BASE64,
        label_x=int(label_x),
        value_x=int(value_x)
    )


def parse_coverage_from_html(html_path):
    """Parse coverage data from gcovr HTML output using regex."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        coverage_data = {
            'lines': None,
            'functions': None,
            'branches': None
        }

        # Find each summary-card and extract type + percentage directly
        # from the full HTML content (avoids fragile summary-section extraction).
        card_pattern = re.compile(
            r'<div class="summary-card">\s*'
            r'<div class="summary-card-header">\s*<h3>(\w+)</h3>\s*</div>\s*'
            r'<div class="summary-card-body">.*?'
            r'<(?:span|div) class="ring-text">([^<]+)</(?:span|div)>',
            re.DOTALL
        )

        for match in card_pattern.finditer(content):
            stat_type = match.group(1).lower()
            percentage_text = match.group(2).strip()

            # Extract numeric percentage (skip "-%" which means no data)
            pct_match = re.search(r'([\d.]+)\s*%', percentage_text)
            if pct_match:
                percentage = float(pct_match.group(1))
                if stat_type == 'lines':
                    coverage_data['lines'] = percentage
                elif stat_type == 'functions':
                    coverage_data['functions'] = percentage
                elif stat_type == 'branches':
                    coverage_data['branches'] = percentage

        return coverage_data
    except Exception as e:
        print(f"Error parsing HTML: {e}", file=sys.stderr)
        return None


def parse_coverage_from_json(json_path):
    """Parse coverage data from gcovr JSON summary output."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # gcovr JSON summary format - keys are at top level
        coverage_data = {
            'lines': None,
            'functions': None,
            'branches': None
        }

        if 'line_percent' in data:
            coverage_data['lines'] = data['line_percent']
        elif 'lines_percent' in data:
            coverage_data['lines'] = data['lines_percent']

        if 'function_percent' in data:
            coverage_data['functions'] = data['function_percent']
        elif 'functions_percent' in data:
            coverage_data['functions'] = data['functions_percent']

        if 'branch_percent' in data:
            coverage_data['branches'] = data['branch_percent']
        elif 'branches_percent' in data:
            coverage_data['branches'] = data['branches_percent']

        return coverage_data
    except Exception as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return None


def generate_badges(output_dir, coverage_data):
    """Generate badge SVG files in the output directory."""
    badges_dir = Path(output_dir) / 'badges'
    badges_dir.mkdir(exist_ok=True)

    badge_configs = [
        ('coverage-lines.svg', 'coverage', coverage_data.get('lines')),
        ('coverage-functions.svg', 'functions', coverage_data.get('functions')),
        ('coverage-branches.svg', 'branches', coverage_data.get('branches')),
    ]

    generated = []
    for filename, label, value in badge_configs:
        if value is not None:
            svg = generate_badge_svg(label, value)
            badge_path = badges_dir / filename
            with open(badge_path, 'w', encoding='utf-8') as f:
                f.write(svg)
            generated.append(filename)
            print(f"Generated {badge_path} ({label}: {value:.1f}%)")
        else:
            print(f"Skipping {filename}: no data available")

    # Also write a JSON summary for potential dynamic badge use
    summary_path = badges_dir / 'coverage.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            'lines': coverage_data.get('lines'),
            'functions': coverage_data.get('functions'),
            'branches': coverage_data.get('branches')
        }, f, indent=2)
    print(f"Generated {summary_path}")

    return generated


def main():
    if len(sys.argv) < 2:
        print("Usage: generate_badges.py <gcovr_output_dir> [--json <summary.json>]", file=sys.stderr)
        print("  Parses index.html or JSON summary to generate coverage badges.", file=sys.stderr)
        sys.exit(1)

    output_dir = sys.argv[1]
    json_path = None

    # Check for --json argument
    if '--json' in sys.argv:
        json_idx = sys.argv.index('--json')
        if json_idx + 1 < len(sys.argv):
            json_path = sys.argv[json_idx + 1]

    if not os.path.isdir(output_dir):
        print(f"Error: {output_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    coverage_data = None

    # Try JSON first if specified
    if json_path and os.path.isfile(json_path):
        print(f"Parsing coverage from JSON: {json_path}")
        coverage_data = parse_coverage_from_json(json_path)

    # Fall back to HTML parsing
    if not coverage_data or all(v is None for v in coverage_data.values()):
        html_path = os.path.join(output_dir, 'index.html')
        if os.path.isfile(html_path):
            print(f"Parsing coverage from HTML: {html_path}")
            coverage_data = parse_coverage_from_html(html_path)

    if not coverage_data or all(v is None for v in coverage_data.values()):
        print("Error: Could not extract coverage data", file=sys.stderr)
        sys.exit(1)

    print(f"Coverage data: lines={coverage_data.get('lines')}, "
          f"functions={coverage_data.get('functions')}, "
          f"branches={coverage_data.get('branches')}")

    generated = generate_badges(output_dir, coverage_data)
    print(f"Successfully generated {len(generated)} badges in {output_dir}/badges/")


if __name__ == '__main__':
    main()
