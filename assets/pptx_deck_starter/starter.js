const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "deck-production-orchestrator";

const slide = pptx.addSlide();
slide.background = { color: "F7FAFC" };
slide.addText("标题放这里", {
  x: 0.8, y: 0.7, w: 8.5, h: 0.6,
  fontFace: "Source Han Sans SC",
  fontSize: 28,
  bold: true,
  color: "0B3C5D"
});
slide.addText("这是 PPTX starter，用于快速验证可编辑输出。", {
  x: 0.8, y: 1.5, w: 6.5, h: 0.5,
  fontFace: "Source Han Sans SC",
  fontSize: 16,
  color: "4D6C82"
});

pptx.writeFile({ fileName: "starter_output.pptx" });
