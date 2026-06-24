import streamlit as st
import subprocess
import tempfile
import shutil
import os
import io
import pandas as pd

st.markdown(
    """
    <style>
    .type-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 300;
        font-size: 3rem;
        text-transform: uppercase;
        letter-spacing: 8px;
        color: #4CC8A3 !important;
        display: inline-block;
        position: relative;
        padding-bottom: 10px;
        margin-bottom: 28px;
    }
    /* underline: draws left → right */
    .type-title::after {
        content: ""; position: absolute; left: 0; bottom: 0;
        height: 3px; width: 0; background: #4CC8A3;
        animation: underline 1s ease forwards;
    }
    /* vertical line at the end: draws top → bottom */
    .type-title::before {
        content: ""; position: absolute; top: 0; right: 0;
        width: 3px; height: 0; background: #4CC8A3;
        animation: draw-vert 1s ease forwards;
    }
    @keyframes underline { to { width: 120% } }
    @keyframes draw-vert { to { height: 120% } }
    </style>
    <h1 class="type-title">intersect</h1>
    """,
    unsafe_allow_html=True,
)

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
            afile.seek(0)
            text_stream = io.TextIOWrapper(afile, encoding="utf-8")
            with open(a_path, "w") as out_fh:
                for line in text_stream:
                    if line.startswith("#"):
                        out_fh.write(line)
                        continue
                    cols = line.rstrip("\n").split("\t")
                    if len(cols) > 2 and (not ftype or ftype == "all" or cols[2] == ftype):
                        out_fh.write(line)
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
