from PyInstaller.utils.hooks import collect_dynamic_libs

# This will auto-collect cp_model_helper.dll/.so and any other
# native libraries under the ortools package.
binaries = collect_dynamic_libs('ortools')