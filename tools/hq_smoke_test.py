import sys
import traceback
import os

# Ensure custom_nodes path is discoverable
CUSTOM_NODES_PATH = r"C:\Users\Baxter\Documents\ComfyUI_env\ComfyUI\custom_nodes"
if os.path.isdir(CUSTOM_NODES_PATH):
    sys.path.insert(0, CUSTOM_NODES_PATH)

def main():
    try:
        import HQ_StemRepair
        print('Imported HQ_StemRepair package:', HQ_StemRepair)

        # import classes
        from HQ_StemRepair import HQ_StemRepair as RepairNode
        from HQ_StemRepair import HQ_SampleExtractor, HQ_Loader

        print('Classes available:', RepairNode, HQ_SampleExtractor, HQ_Loader)

        # instantiate
        r = RepairNode()
        s = HQ_SampleExtractor()
        l = HQ_Loader()
        print('Instantiated nodes:', type(r).__name__, type(s).__name__, type(l).__name__)

        # call skeleton methods
        sample_out = s.extract_samples("")
        print('HQ_SampleExtractor.extract_samples() ->', sample_out)

        loader_out = l.load_files('Single File', file='C:\\Windows\\notepad.exe')
        print("HQ_Loader.load_files('Single File', file=...) ->", loader_out)

    except Exception:
        traceback.print_exc()
        sys.exit(2)

if __name__ == '__main__':
    main()
