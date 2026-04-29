import sys
import os
import traceback

def main():
    try:
        # Path to ComfyUI custom_nodes parent (use forward slashes to avoid unicodeescape issues)
        pkg_root = "c:/Users/Baxter/Documents/ComfyUI_env/ComfyUI"
        if pkg_root not in sys.path:
            sys.path.insert(0, pkg_root)

        print('sys.path includes:', sys.path[0])

        import importlib
        pkg = importlib.import_module('custom_nodes.HQ_StemRepair')
        print('Imported package:', pkg)

        # Try submodule imports and instantiation
        from custom_nodes.HQ_StemRepair.HQ_StemRepair import HQ_StemRepair
        from custom_nodes.HQ_StemRepair.HQ_SampleExtractor import HQ_SampleExtractor
        from custom_nodes.HQ_StemRepair.HQ_Loader import HQ_Loader

        hr = HQ_StemRepair()
        se = HQ_SampleExtractor()
        ld = HQ_Loader()

        print('Instantiated HQ_StemRepair:', type(hr))
        print('Instantiated HQ_SampleExtractor:', type(se))
        print('Instantiated HQ_Loader:', type(ld))

        print('SMOKE TEST SUCCESS')
    except Exception:
        print('SMOKE TEST FAILED')
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
