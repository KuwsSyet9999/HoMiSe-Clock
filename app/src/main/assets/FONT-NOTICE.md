# 字体说明与许可

本应用内置的数码管字体分两部分，许可均为 **SIL Open Font License 1.1**。

## HSSeg 7（七段，24 个 TTF）

由 [DSEG](http://www.keshikan.net) v0.46 的七段字体派生修改而来，许可证原文见同目录
`DSEG-LICENSE.txt`。

对原版的修改：

- 字体家族名改为 `HSSeg 7 <变体>`，PostScript 名改为 `HSSeg7<变体>-<字重>`，版本号独立维护；
  不再使用 DSEG 的 Reserved Font Name（OFL 1.1 第 3 条要求）。
- 字符 `R` / `r` 的段位改为 `b e f g`（原版 `b c e f g`）。
- 补齐 `colon`、`period` 的轮廓（FontForge 重新生成时会丢失）。
- 全部字符轮廓按 `segments-7.csv` 的段位表重建，避免生成器简化笔迹。
- 版权声明保留原作者，并追加修改声明：
  `Modifications copyright (c) 2026, HoMiSe APP.`

## 十四段（24 个 TTF）与 7SEGG-CHAN / Weather

仍为 DSEG v0.46 原版字形，未作修改，随附同一份 OFL 许可。

## 分发要求

OFL 1.1 允许把字体随应用一起分发，条件是每份副本都带有上述版权声明与许可全文。
`assets/DSEG-LICENSE.txt` 即该全文；字体内部 `name` 表的版权与许可字段也指向它。
