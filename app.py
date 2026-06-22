"""
TakeMeter — r/nba Discourse Classifier
Gradio interface for the fine-tuned DistilBERT model.

Usage:
    python app.py --model_path /path/to/your/model/folder

The model folder should contain config.json, tokenizer files, and model weights
(pytorch_model.bin or model.safetensors) as saved by HuggingFace Trainer.
"""

import argparse
import gradio as gr
import torch
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer

LABEL_NAMES = ["analysis", "hot_take", "reaction"]

LABEL_DESCRIPTIONS = {
    "analysis": "Makes a real argument with actual evidence — stats, historical comparisons, tactical observations.",
    "hot_take": "Bold opinion with no real supporting evidence. Asserts rather than argues.",
    "reaction": "Pure emotion about something that just happened. No argument, just feeling.",
}

EXAMPLES = [
    "Jokic's assist-to-turnover ratio this playoff run (5.8) is the best ever recorded for a center through 10+ games.",
    "LeBron is not a top 5 player of all time and his fans need to accept it. MJ, Kareem, Magic were all better. No debate.",
    "CURRY JUST HIT THAT FROM HALF COURT ARE YOU KIDDING ME",
    "The Warriors' net rating drops 14.2 points per 100 possessions when Draymond is off the floor. Their entire defensive system collapses without him.",
    "Giannis will never win a championship without a legitimate second star. He's Karl Malone 2.0.",
]

model = None
tokenizer = None


def load_model(model_path: str):
    global model, tokenizer
    tokenizer = DistilBertTokenizer.from_pretrained(model_path)
    model = DistilBertForSequenceClassification.from_pretrained(model_path)
    model.eval()


def classify(text: str):
    if not text.strip():
        return {label: 0.0 for label in LABEL_NAMES}, "Enter a post above."

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1).squeeze().tolist()

    scores = {LABEL_NAMES[i]: round(probs[i], 4) for i in range(len(LABEL_NAMES))}
    top_label = max(scores, key=scores.get)
    confidence = scores[top_label]

    explanation = (
        f"**Predicted: {top_label}** ({confidence:.1%} confidence)\n\n"
        f"{LABEL_DESCRIPTIONS[top_label]}"
    )
    return scores, explanation


def build_ui():
    with gr.Blocks(title="TakeMeter — r/nba Discourse Classifier") as demo:
        gr.Markdown(
            "# TakeMeter\n"
            "Paste an r/nba post or comment and the model will classify it as "
            "**analysis**, **hot_take**, or **reaction**."
        )

        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="Post or comment",
                    placeholder="Paste an r/nba post here...",
                    lines=4,
                )
                submit_btn = gr.Button("Classify", variant="primary")

            with gr.Column(scale=1):
                label_output = gr.Label(
                    label="Confidence scores", num_top_classes=3
                )

        explanation_output = gr.Markdown(label="Result")

        gr.Examples(
            examples=[[ex] for ex in EXAMPLES],
            inputs=text_input,
            label="Try these examples",
        )

        submit_btn.click(
            fn=classify,
            inputs=text_input,
            outputs=[label_output, explanation_output],
        )
        text_input.submit(
            fn=classify,
            inputs=text_input,
            outputs=[label_output, explanation_output],
        )

    return demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="Path to the fine-tuned model directory (from HuggingFace Trainer save).",
    )
    args = parser.parse_args()

    print(f"Loading model from {args.model_path}...")
    load_model(args.model_path)
    print("Model loaded. Starting Gradio...")

    demo = build_ui()
    demo.launch()
