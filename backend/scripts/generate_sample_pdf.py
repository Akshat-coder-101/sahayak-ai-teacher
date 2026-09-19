import os
import io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pypdf

def generate_sample_science_pdf(output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    pages_data = [
        {
            "title": "Chapter 1: The Bio-Energetics of Life & Photosynthesis",
            "sections": [
                "1.1 Overview of Solar Energy Conversion",
                "Photosynthesis is the fundamental biological process through which autotrophic organisms convert solar photons into chemical energy stored in glucose molecules. The overall balanced chemical equation is 6CO2 + 6H2O + Light Energy -> C6H12O6 + 6O2.",
                "1.2 The Light-Dependent Reactions",
                "Within the thylakoid membranes of chloroplasts, photon absorption occurs in two multi-protein complexes: Photosystem II (P680) and Photosystem I (700). Water molecules undergo photolysis, releasing electrons, protons (H+ ions), and oxygen gas as a byproduct. The electron transport chain pumps protons into the thylakoid lumen, creating an electrochemical gradient that drives ATP synthase.",
                "1.3 Chlorophyll Pigments and Common Misconceptions",
                "Key Concept: Chlorophyll a and chlorophyll b absorb blue (430-450 nm) and red (640-660 nm) wavelengths. A frequent student misconception is believing plants appear green because they absorb green light. In reality, plants appear green because chlorophyll cannot efficiently absorb green photons (500-550 nm), reflecting and transmitting them back to our eyes."
            ]
        },
        {
            "title": "Chapter 2: The Calvin Cycle and Carbon Fixation",
            "sections": [
                "2.1 The Light-Independent Reactions (Dark Reactions)",
                "The chemical energy produced in the light reactions (ATP and NADPH) is utilized in the stroma of chloroplasts during the Calvin Cycle to synthesize sugars from inorganic carbon dioxide (CO2).",
                "2.2 Three Major Phases of the Calvin Cycle",
                "Phase 1 - Carbon Fixation: The enzyme RuBisCO (Ribulose-1,5-bisphosphate carboxylase-oxygenase) catalyzes the attachment of CO2 to the 5-carbon sugar RuBP, forming two molecules of 3-phosphoglycerate (3-PGA).",
                "Phase 2 - Reduction: ATP and NADPH donate phosphate groups and high-energy electrons to convert 3-PGA into glyceraldehyde-3-phosphate (G3P). For every three turns of the cycle, one net G3P molecule exits to synthesize glucose.",
                "Phase 3 - Regeneration of RuBP: The remaining five G3P molecules are re-arranged using additional ATP into three molecules of RuBP, enabling the cycle to sustain continuous carbon fixation."
            ]
        },
        {
            "title": "Chapter 3: Cellular Respiration & ATP Production",
            "sections": [
                "3.1 Aerobic Respiration Overview",
                "While photosynthesis stores solar energy into carbohydrates, cellular respiration breaks down organic molecules in the presence of oxygen to produce universal cellular fuel: Adenosine Triphosphate (ATP). The chemical formula is C6H12O6 + 6O2 -> 6CO2 + 6H2O + 30-32 ATP.",
                "3.2 The Four Metabolic Stages",
                "Stage 1 - Glycolysis: Occurs in the cytoplasm without oxygen, splitting 1 glucose into 2 pyruvate molecules, yielding a net 2 ATP and 2 NADH.",
                "Stage 2 - Pyruvate Oxidation: Pyruvate transitions into the mitochondrial matrix, releasing CO2 and producing Acetyl-CoA.",
                "Stage 3 - Citric Acid (Krebs) Cycle: Acetyl-CoA is oxidized, generating electron carriers 6 NADH, 2 FADH2, and 2 ATP per glucose.",
                "Stage 4 - Oxidative Phosphorylation: Inner mitochondrial membrane cytochromes accept electrons, transferring them to oxygen to form H2O, generating 26-28 ATP via chemiosmotic ATP Synthase."
            ]
        }
    ]

    with PdfPages(output_path) as pdf:
        for page_idx, page in enumerate(pages_data):
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis('off')
            
            # Draw header bar
            y_pos = 0.93
            ax.text(0.08, y_pos, page["title"], fontsize=14, weight='bold', color='#1e3a8a')
            y_pos -= 0.03
            ax.plot([0.08, 0.92], [y_pos, y_pos], color='#3b82f6', linewidth=2)
            y_pos -= 0.05
            
            for section in page["sections"]:
                if section.startswith("1.") or section.startswith("2.") or section.startswith("3.") or section.startswith("Phase") or section.startswith("Stage"):
                    ax.text(0.08, y_pos, section, fontsize=11, weight='bold', color='#1f2937')
                    y_pos -= 0.035
                else:
                    # Wrap paragraph lines cleanly
                    words = section.split()
                    lines = []
                    current_line = []
                    for word in words:
                        current_line.append(word)
                        if len(" ".join(current_line)) > 78:
                            lines.append(" ".join(current_line))
                            current_line = []
                    if current_line:
                        lines.append(" ".join(current_line))
                    
                    for line_str in lines:
                        ax.text(0.08, y_pos, line_str, fontsize=9.5, color='#374151')
                        y_pos -= 0.024
                    y_pos -= 0.02
            
            # Footer
            ax.text(0.5, 0.04, f"Public Domain Educational Sample — Page {page_idx + 1} of {len(pages_data)}", 
                    fontsize=8, color='#9ca3af', ha='center')
            
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

    print(f"Successfully generated sample science PDF at: {output_path}")

if __name__ == "__main__":
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_file = os.path.join(repo_root, "samples", "photosynthesis_chapter.pdf")
    generate_sample_science_pdf(out_file)
