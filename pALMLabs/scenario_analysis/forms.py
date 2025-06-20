from django import forms
import pandas as pd


class ScenarioUploadForm(forms.Form):
    # Only mapping_file is handled by the Django form
    mapping_file = forms.FileField(
        label="Scenario Mapping File (CSV: filename, scenario_name)",
        required=True,
    )

    def clean_mapping_file(self):
        mapping_file = self.cleaned_data.get("mapping_file")

        try:
            df = pd.read_csv(mapping_file)
        except Exception as e:
            raise forms.ValidationError(f"Could not read mapping file: {e}")

        if "filename" not in df.columns or "scenario_name" not in df.columns:
            raise forms.ValidationError(
                "Mapping file must contain 'filename' and 'scenario_name' columns."
            )

        if any("/" in fname or "\\" in fname for fname in df["filename"]):
            raise forms.ValidationError(
                "Filenames must not include folder paths — just the name."
            )

        mapping_file.seek(0)  # Reset pointer for reuse later
        return mapping_file
