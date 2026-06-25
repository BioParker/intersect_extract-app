import streamlit as st
import subprocess
import tempfile
import shutil
import os
import io
import pandas as pd

def animated_title(word: str):
    key = "".join(ch for ch in word.lower() if ch.isalnum())  # css-safe suffix
    steps = len(word)
    st.markdown(
        f"""
        <style>
        .type-wrap-{key} {{
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 300;
            font-size: 3rem;
            text-transform: uppercase;
            letter-spacing: 8px;
            color: #4CC8A3 !important;
            position: relative;
            display: inline-block;
            padding-bottom: 10px;
            margin: 0 0 28px 0;
            line-height: 1.1;
        }}

        .type-wrap-{key} .ghost {{ visibility: hidden; }}

        .type-wrap-{key} .type-title {{
            position: absolute;
            left: 0;
            top: 0;
            white-space: nowrap;
            overflow: hidden;
            width: 0;
            animation: typing-{key} 1.4s steps({steps}, end) forwards;
        }}

        @keyframes typing-{key} {{ to {{ width: 100%; }} }}

        .type-wrap-{key}::after {{
            content: ""; position: absolute; left: 0; bottom: 0;
            height: 3px; width: 0; background: #4CC8A3;
            animation: underline-{key} 1s ease forwards;
            animation-delay: 1.4s;
        }}
        .type-wrap-{key}::before {{
            content: ""; position: absolute; top: 0; right: 0;
            width: 3px; height: 0; background: #4CC8A3;
            animation: draw-vert-{key} 1s ease forwards;
            animation-delay: 1.4s;
        }}
        @keyframes underline-{key} {{ to {{ width: 120%; }} }}
        @keyframes draw-vert-{key} {{ to {{ height: 120%; }} }}
        </style>

        <h1 class="type-wrap-{key}">
            <span class="ghost">{word}</span>
            <span class="type-title">{word}</span>
        </h1>
        """,
        unsafe_allow_html=True,
    )
def animated_title_boxed(word: str):
    key = "".join(ch for ch in word.lower() if ch.isalnum())  # css-safe suffix
    st.markdown(
        f"""
        <style>
        .type-outer-{key} {{
            margin-bottom: 40px;         /* gap below the box — block-level, reliably pushes next container */
        }}
        .type-wrap-{key} {{
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 300;
            font-size: 3rem;
            text-transform: uppercase;
            letter-spacing: 8px;
            color: #4CC8A3 !important;
            position: relative;
            display: inline-block;       /* stays inline-block so the box sizes to the text */
            padding: 12px 16px;          /* breathing room so the box clears the letters */
            margin: 0;                   /* margin now lives on the wrapping div */
            line-height: 1.1;
        }}
        .type-wrap-{key} .ghost {{
            visibility: hidden;
            margin-right: -8px;          /* cancel trailing letter-spacing so the box centres */
        }}
        .type-wrap-{key} .type-title {{
            position: absolute;
            left: 16px;                  /* match padding so it sits over the ghost */
            top: 12px;
            white-space: nowrap;
            opacity: 0;                  /* start invisible, fade in */
            animation: fade-{key} 1.2s ease forwards;
        }}
        @keyframes fade-{key} {{ to {{ opacity: 1; }} }}
        /* four box sides, drawn in sequence once the fade finishes (1.2s) */
        .type-wrap-{key} .bx {{ position: absolute; background: #4CC8A3; }}
        /* 1. bottom: left → right */
        .type-wrap-{key} .bx-bottom {{
            left: 0; bottom: 0; height: 3px; width: 0;
            animation: bx-h-{key} 0.45s ease forwards;
            animation-delay: 1.2s;
        }}
        /* 2. right: bottom → top */
        .type-wrap-{key} .bx-right {{
            right: 0; bottom: 0; width: 3px; height: 0;
            animation: bx-v-{key} 0.45s ease forwards;
            animation-delay: 1.65s;
        }}
        /* 3. top: right → left */
        .type-wrap-{key} .bx-top {{
            right: 0; top: 0; height: 3px; width: 0;
            animation: bx-h-{key} 0.45s ease forwards;
            animation-delay: 2.1s;
        }}
        /* 4. left: top → bottom */
        .type-wrap-{key} .bx-left {{
            left: 0; top: 0; width: 3px; height: 0;
            animation: bx-v-{key} 0.45s ease forwards;
            animation-delay: 2.55s;
        }}
        @keyframes bx-h-{key} {{ to {{ width: 100%; }} }}
        @keyframes bx-v-{key} {{ to {{ height: 100%; }} }}
        </style>
        <div class="type-outer-{key}">
            <h1 class="type-wrap-{key}">
                <span class="ghost">{word}</span>
                <span class="type-title">{word}</span>
                <span class="bx bx-bottom"></span>
                <span class="bx bx-right"></span>
                <span class="bx bx-top"></span>
                <span class="bx bx-left"></span>
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

#with st.container(border=True):
#    st.badge("Select Mode", color="primary")
#    mode = st.segmented_control("Mode",
#                                ["Intersect","Extract"])

def mode_selector():
    if "mode" not in st.session_state:
        st.session_state.mode = "Intersect"      # default

    st.markdown(
        """
        <style>
        div[data-testid="stButton"] > button {
            width: 100%;
            height: 88px;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 300;
            font-size: 1.5rem;
            text-transform: uppercase;
            letter-spacing: 6px;
            border-radius: 4px;
            transition: all 0.25s ease;
        }
        /* active mode = filled teal, glowing */
        div[data-testid="stButton"] > button[kind="primary"] {
            background: #4CC8A3;
            color: #0E1117;
            border: 2px solid #4CC8A3;
            box-shadow: 0 0 20px rgba(76, 200, 163, 0.45);
        }
        /* inactive mode = dim teal outline */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent;
            color: #4CC8A3;
            border: 2px solid #4CC8A3;
            opacity: 0.5;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            opacity: 1;
            transform: translateY(-2px);
            box-shadow: 0 0 16px rgba(76, 200, 163, 0.3);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            "Intersect", key="btn_intersect", use_container_width=True,
            type="primary" if st.session_state.mode == "Intersect" else "secondary",
        ):
            st.session_state.mode = "Intersect"
            st.rerun()
    with c2:
        if st.button(
            "Extract", key="btn_extract", use_container_width=True,
            type="primary" if st.session_state.mode == "Extract" else "secondary",
        ):
            st.session_state.mode = "Extract"
            st.rerun()

    return st.session_state.mode

mode = mode_selector()

if mode == "Intersect":
    animated_title("intersect")

    st.markdown(
        "<div style='margin-top:24px; margin-bottom:24px;'>"
        "For a full explanation of bedtools intersect options, see "
        "<a href='https://bedtools.readthedocs.io/en/latest/content/tools/intersect.html' "
        "target='_blank'>here</a></div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.badge("-a", color="primary")
        st.caption("Set of features to filter, BED or GTF file")
        afile = st.file_uploader("*a-file", type=["bed", "gtf"],label_visibility="collapsed")

    if afile and os.path.splitext(afile.name)[1] == ".gtf":
        with st.container(border=True):
            df = pd.read_csv(afile, sep="\t", header=None, comment="#", usecols=[2])
            feature_types = ["all"] + sorted(df[2].unique())
            st.badge("Feature type", color="primary")
            st.caption("Select feature type from -a to extract")
            ftype = st.selectbox("Select feature type",
                                  feature_types)

    with st.container(border=True):
        st.badge("-b", color="primary")
        st.caption("Features to intersect against. Please provide a single set of coordinates or a file in an appropriate format (BED/GTF)")
        boption = st.segmented_control("boption",
                                   ["coordinates", "file"],
                                       label_visibility="collapsed")
        if boption == "coordinates":
            coordinates = st.text_input("Input coordinates to intersect with **-a** in the format *chr:start-end*, 1-based")
        elif boption == "file":
            bfile = st.file_uploader("*b-file", type=["bed", "gtf"], label_visibility="collapsed")

    dofrac = st.toggle("Toggle for the -f option, which sets the minimum required overlap fraction",
                       False)

    recip = False
    if dofrac:
        recip = st.toggle("Toggle for the -r option, which determines whether the -f fraction is reciprocal"
                           "\nFor exact matches, use -r and set the -f slider to 1",
                           False)
        f = st.slider("-f",
                      min_value=0.0,
                      max_value=1.0,
                      width=100)
    else:
        f = None

    strand = st.toggle("Toggle for the -s option, which enforces strand matching",
                       False)

    st.divider()
    run = st.button("Run intersect", type="primary")

    #--------------------------- run -----------------------------------#

    if run:
        # --- validate ---
        if afile is None:
            st.error("Upload an -a file first.")
            st.stop()
        if boption is None:
            st.error("Choose a -b input: coordinates or a BED file.")
            st.stop()
        if shutil.which("bedtools") is None:
            st.error("bedtools isn't on PATH — activate the conda env that has it.")
            st.stop()

        with tempfile.TemporaryDirectory() as td:
            # stage -a, keeping its extension so bedtools detects BED vs GTF
            a_suffix = os.path.splitext(afile.name)[1] or ".bed"
            if a_suffix == ".gtf":
                a_path = os.path.join(td, "a.gtf")
                atext = afile.getvalue().decode(encoding="utf-8")
                with open(a_path, "w") as out_fh:
                    for line in atext.splitlines():
                        if line.startswith("#"):
                            out_fh.write(line + "\n")
                            continue
                        cols = line.split("\t")
                        if len(cols) > 2 and (not ftype or ftype == "all" or cols[2] == ftype):
                            out_fh.write(line + "\n")
            else:
                a_path = os.path.join(td, "a" + a_suffix)
                with open(a_path, "wb") as fh:
                    fh.write(afile.getvalue())

            # build -b
            b_path = os.path.join(td, "b.bed")
            if boption == "coordinates":
                try:
                    s = coordinates.strip().replace(",", "")
                    chrom, _, rng = s.partition(":")
                    start_s, _, end_s = rng.partition("-")
                    start1, end1 = int(start_s), int(end_s)
                    if not chrom or end1 < start1:
                        raise ValueError
                except (ValueError, AttributeError):
                    st.error("Coordinates must look like chr:start-end, e.g. chr1:1000-2000.")
                    st.stop()
                # convert coordinates to BED format
                with open(b_path, "w") as fh:
                    fh.write(f"{chrom}\t{start1 - 1}\t{end1}\n")
            else:  # "bed/gtf"
                if bfile is None:
                    st.error("Upload a -b BED/GTF file.")
                    st.stop()
                with open(b_path, "wb") as fh:
                    fh.write(bfile.getvalue())


            # --- build command for subprocess ---
            cmd = ["bedtools", "intersect", "-a", a_path, "-b", b_path, "-u"]
            if f:            # check f truthiness  - None or 0.0 -> omit (bedtools needs -f > 0)
                cmd += ["-f", str(f)]
            if recip:
                cmd += ["-r"]
            if strand:
                cmd += ["-s"]

            #making user-readable header
            b_label = bfile.name if boption == "file" else coordinates
            pheader = ["bedtools", "intersect", "-a", afile.name, "-b", b_label, "-u"]
            if f:      pheader += ["-f", str(f)]
            if recip:  pheader += ["-r"]
            if strand: pheader += ["-s"]
            # --- run ---
            proc = subprocess.run(cmd, capture_output=True, text=True)
            st.session_state["result"] = {
                "cmd": " ".join(pheader),
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "rc": proc.returncode,
                "ext": a_suffix.lstrip(".") or "bed",
            }

    # --- show last result (kept in session_state so it survives the download rerun) ---
    res = st.session_state.get("result")
    if res:
        st.code(res["cmd"], language="bash")
        if res["rc"] != 0:
            st.error(f"bedtools exited with code {res['rc']}")
        if res["stderr"].strip():
            st.warning(res["stderr"].strip())
        out = res["stdout"]
        n = out.count("\n") if out.strip() else 0
        st.caption(f"{n} feature(s) retained")
        if out.strip():
            header = f"# $intersect-app {res['cmd']}\n"
            st.download_button("Download", header + out, file_name=f"intersect.{res['ext']}")
        st.code(out or "(no overlaps)", language="text")

if mode == "Extract":
    animated_title_boxed("Extract")

    with st.container(border=True):
        st.badge("GTF", color="primary")
        st.caption("GTF file to extract from")
        egtf = st.file_uploader("*gtf-file", type=["gtf"],label_visibility="collapsed")

    if egtf:
        with st.container(border=True):
            gtf_txt = egtf.getvalue().decode(encoding="utf-8")
            attr_name = set()
            feats = set()
            for line in gtf_txt.splitlines():
                # set comprehension. We create an empty set above, take our line,
                # strip, split on tab, get attributes column ([8]) and split on ';',
                # check truthiness - attributes end on ';' so we have to check
                # truthiness to escape the field that contains the empty string
                # produced by splitting on a terminal delimiter - and then strip
                # again, followed by a split on a whitespace with maxsplit = 1,
                # meaning that only 1 split occurs at the first whitespace, which
                # leaves the first element as our attribute name, as the attribute
                # names and values are separated by a whitespace. This set comprehension
                # generates a set which is then merged into the attr_name set using update()
                # and because sets cannot contain duplicated values, the final attr_names
                # gives the full set of unique attribute names in the GTF
                if line.startswith("#"):
                    continue
                cols = line.split("\t")
                if len(cols) < 9:
                    continue
                feats.add(cols[2])
                attr_name.update({attr.strip().split(' ', 1)[0]
                                  for attr in cols[8].split(';')
                                  if attr.strip()})
            feats = ["all"] + sorted(feats)
            st.badge("Feature type", color="primary")
            st.caption("Select feature type to extract - if the selected feature lacks the selected attribute, an error will be thrown")
            ftype = st.selectbox("Select feature type",
                                  feats,
                                  label_visibility="collapsed")
            st.badge("Attributes field", color="primary")
            st.caption("Select attribute field to filter on")
            atype = st.selectbox("Select field",
                                  attr_name,
                                  label_visibility="collapsed")

            with st.container(border=True):
                st.badge("Attribute values", color="primary")
                st.caption(f"Input a single value, or a text file with one value per line."
                           f" Every line whose **{atype}** attribute matches the provided value will be extracted.")
                voption = st.segmented_control("voption",
                                              ["text input", "file"],
                                               label_visibility="collapsed")
                if voption == "text input":
                    text_input = st.text_input(
                        "Please provide a single value")
                elif voption == "file":
                    vfile = st.file_uploader("v-file", type=["txt"], label_visibility="collapsed")

    st.divider()
    run = st.button("Run Extract", type="primary")

    if run:
        # --- validate ---
        if egtf is None:
            st.error("Upload a GTF file first.")
            st.stop()
        if voption is None:
            st.error("Please provide values to filter attributes")
            st.stop()
        if voption == "file":
            if vfile is None:
                st.error("Upload a values file.")
                st.stop()

        vlist=set()
        if voption == "text input":
            vlist.add(text_input.rstrip())
        if voption == "file":
            vinstream = vfile.getvalue().decode(encoding="utf-8")
            for line in vinstream.splitlines():
                vlist.add(line.rstrip())

        gtf_txt = egtf.getvalue().decode(encoding="utf-8")
        outlines=[]
        for line in gtf_txt.splitlines():
            if line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) < 9:
                continue
            if cols[2] == ftype or ftype == "all":
                for attr in cols[8].split(';'):
                    if attr.strip():
                        aname, _, aval = attr.strip().partition(" ")
                        if aname == atype and aval.strip().strip('"') in vlist:
                            outlines.append(line.rstrip("\n"))

        # --- display + download --- #
        output = "\n".join(outlines)
        n = len(outlines)
        st.caption(f"{n} row(s) matched")
        if outlines:
            header = f"# extract-app  {atype} in {sorted(vlist)}\n"
            st.download_button("Download", header + output + "\n",
                               file_name="extracted.gtf")
            st.code(output, language="text")
        else:
            st.code("(no matching rows)", language="text")








