<p align="center">
  <img src="docs/assets/hero.svg" alt="TeslaSkin — 用文字制作 Model Y 和 Model 3 车机皮肤" width="100%" />
</p>

<p align="center">
  <strong>一句话，让你的 Tesla 换上喜欢的皮肤。</strong><br />
  不用提供参考图，告诉它主题，剩下的设计交给 TeslaSkin。
</p>

<p align="center">
  <a href="https://github.com/isunky/TeslaSkin/releases/latest"><img src="https://img.shields.io/github/v/release/isunky/TeslaSkin?style=flat-square&amp;labelColor=17232d&amp;color=e9b77f" alt="最新版本" /></a>
  <img src="https://img.shields.io/badge/Model_Y_%26_Model_3-车机皮肤-e9b77f?style=flat-square&amp;labelColor=17232d" alt="Model Y 和 Model 3 车机皮肤" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-9daab5?style=flat-square&amp;labelColor=17232d" alt="Apache 2.0" /></a>
</p>

<p align="center">
  <a href="#安装">安装</a> · <a href="#使用">使用</a> · <a href="#制作流程">制作流程</a> · <a href="#作品示例">作品示例</a>
</p>

---

> **推荐在支持 Skill、内置生图和文件处理的 ChatGPT 环境中使用。** 这样可以在同一段对话里生成、调整并交付皮肤。不同客户端的能力可能不同；请以当前环境提供的功能为准。

## 安装

在支持安装 Skill 的助手中（例如 Codex），发送以下提示词：

```text
请从 https://github.com/isunky/TeslaSkin 安装最新版 tesla-skin Skill。
技能位于仓库的 skills/tesla-skin 目录，请安装到当前环境的个人 skills 目录，
检查所需依赖。如果已经安装，请先备份已有的自定义内容，再更新到最新版。
```

安装完成后，开启新对话或按客户端提示刷新，即可使用。如果当前环境不支持通过对话安装，可从 [Releases 下载最新技能包](https://github.com/isunky/TeslaSkin/releases/latest)，并按客户端的 Skill 安装方式导入。

## 使用

描述你想要的主题即可，例如：

```text
用 $tesla-skin 生成一款 Model 3 橘猫主题皮肤。
```

TeslaSkin 会自动补充配色、图案和细节，生成后还可以继续说：

```text
颜色再淡一点，只修改引擎盖。
```

支持内置白版对应的 Model Y 和 Model 3；不指定车型时会分别生成两款皮肤。生成的图片通过文件检查后，仍需在 App 和车辆上确认展示效果。

## 制作流程

先生成整车概念图，再制作各车型的皮肤展开图，分别检查设计效果和文件规格。点击图片可查看原图。

[![TeslaSkin 皮肤制作全流程：整车设计、画稿与模板合成、验收交付与反馈](docs/assets/workflow.png)](docs/assets/workflow.png)

## 作品示例

以下提示词保留用户的原始输入；每款展示最新版本的皮肤展开图。标为“候选”的作品仍有图案或接缝细节待确认；所有作品的 App 和实车效果均待验证。

### Model Y

<table>
  <tr>
    <td width="50%" align="center"><strong>Hello Kitty</strong><br /><code>生成一款helloKetty的皮肤</code></td>
    <td width="50%" align="center"><strong>橘猫</strong><br /><code>生成橘猫主题皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-y/hello-kitty.png"><img src="examples/model-y/hello-kitty.png" alt="Hello Kitty 主题皮肤成品展开图" width="420" /></a></td>
    <td align="center"><a href="examples/model-y/orange-cat.png"><img src="examples/model-y/orange-cat.png" alt="橘猫主题皮肤成品展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>鹦鹉</strong><br /><code>生成鹦鹉主题皮肤</code></td>
    <td width="50%" align="center"><strong>超级飞侠</strong><br /><code>生成超级飞侠主题皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-y/parrot.png"><img src="examples/model-y/parrot.png" alt="鹦鹉主题皮肤成品展开图" width="420" /></a></td>
    <td align="center"><a href="examples/model-y/superwings.png"><img src="examples/model-y/superwings.png" alt="超级飞侠主题皮肤成品展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>萌可</strong><br /><code>做一套Model Y萌可主题的皮肤</code></td>
    <td width="50%" align="center"><strong>五月天 · 参考图创作</strong><br /><code>参考图片重新做一套五月天主题的皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-y/teenieping.png"><img src="examples/model-y/teenieping.png" alt="萌可 Model Y 主题皮肤成品展开图" width="420" /></a></td>
    <td align="center"><a href="examples/model-y/mayday.png"><img src="examples/model-y/mayday.png" alt="五月天橙黑赛车风 Model Y 皮肤成品展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>特警</strong><br /><code>做一套特警主题的皮肤</code></td>
    <td width="50%" align="center"><strong>风暴战车</strong><br /><code>做一套金属质感酷炫风暴战车主题的皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-y/swat.png"><img src="examples/model-y/swat.png" alt="特警 Model Y 皮肤展开图" width="420" /></a></td>
    <td align="center"><a href="examples/model-y/storm.png"><img src="examples/model-y/storm.png" alt="风暴战车 Model Y 皮肤展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>包警长 · 候选</strong><br /><code>做一套超级飞侠包警长主题的皮肤</code></td>
    <td width="50%" align="center"><strong>露探长 · 候选</strong><br /><code>做一套全新风格的超级飞侠露探长主题的皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-y/paul.png"><img src="examples/model-y/paul.png" alt="包警长 Model Y 皮肤展开图" width="420" /></a></td>
    <td align="center"><a href="examples/model-y/lucie.png"><img src="examples/model-y/lucie.png" alt="露探长 Model Y 皮肤展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>五月天 · 粉蓝卡丁车</strong><br /><code>再做一个五月天痛车主题的皮肤。</code></td>
    <td width="50%" align="center"><strong>五月天 · 海浪</strong><br /><code>再根据这个图片做一套五月天痛车主题皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-y/mayday-candy.png"><img src="examples/model-y/mayday-candy.png" alt="五月天 · 粉蓝卡丁车 Model Y 皮肤展开图" width="420" /></a></td>
    <td align="center"><a href="examples/model-y/mayday-wave.png"><img src="examples/model-y/mayday-wave.png" alt="五月天 · 海浪 Model Y 皮肤展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>五月天 · 成名在望 · 候选</strong><br /><code>再做一套五月天主题皮肤，尽可能参考图片的布局和图案。</code></td>
    <td width="50%"></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-y/mayday-fame.png"><img src="examples/model-y/mayday-fame.png" alt="五月天 · 成名在望 Model Y 皮肤展开图" width="420" /></a></td>
    <td></td>
  </tr>
</table>

### Model 3

<table>
  <tr>
    <td width="50%" align="center"><strong>超级飞侠</strong><br /><code>用现有素材做一套model 3 超级飞侠的主题皮肤。</code><br />随后调整车头和车尾的对称性。</td>
    <td width="50%" align="center"><strong>五月天 · 参考图创作</strong><br /><code>参考图片重新做一套五月天主题的皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-3/superwings.png"><img src="examples/model-3/superwings.png" alt="超级飞侠 Model 3 皮肤成品展开图" width="420" /></a></td>
    <td align="center"><a href="examples/model-3/mayday.png"><img src="examples/model-3/mayday.png" alt="五月天橙黑赛车风 Model 3 皮肤成品展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>特警</strong><br /><code>做一套特警主题的皮肤</code></td>
    <td width="50%" align="center"><strong>风暴战车</strong><br /><code>做一套金属质感酷炫风暴战车主题的皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-3/swat.png"><img src="examples/model-3/swat.png" alt="特警 Model 3 皮肤展开图" width="420" /></a></td>
    <td align="center"><a href="examples/model-3/storm.png"><img src="examples/model-3/storm.png" alt="风暴战车 Model 3 皮肤展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>包警长 · 候选</strong><br /><code>做一套超级飞侠包警长主题的皮肤</code></td>
    <td width="50%" align="center"><strong>露探长 · 候选</strong><br /><code>做一套全新风格的超级飞侠露探长主题的皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-3/paul.png"><img src="examples/model-3/paul.png" alt="包警长 Model 3 皮肤展开图" width="420" /></a></td>
    <td align="center"><a href="examples/model-3/lucie.png"><img src="examples/model-3/lucie.png" alt="露探长 Model 3 皮肤展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>五月天 · 粉蓝卡丁车</strong><br /><code>再做一个五月天痛车主题的皮肤。</code></td>
    <td width="50%" align="center"><strong>五月天 · 海浪</strong><br /><code>再根据这个图片做一套五月天痛车主题皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-3/mayday-candy.png"><img src="examples/model-3/mayday-candy.png" alt="五月天 · 粉蓝卡丁车 Model 3 皮肤展开图" width="420" /></a></td>
    <td align="center"><a href="examples/model-3/mayday-wave.png"><img src="examples/model-3/mayday-wave.png" alt="五月天 · 海浪 Model 3 皮肤展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>五月天 · 成名在望 · 候选</strong><br /><code>再做一套五月天主题皮肤，尽可能参考图片的布局和图案。</code></td>
    <td width="50%"></td>
  </tr>
  <tr>
    <td align="center"><a href="examples/model-3/mayday-fame.png"><img src="examples/model-3/mayday-fame.png" alt="五月天 · 成名在望 Model 3 皮肤展开图" width="420" /></a></td>
    <td></td>
  </tr>
</table>

---

项目代码与文档遵循 [Apache License 2.0](LICENSE)。示例中的角色和相关品牌属于各自权利人；本项目为独立社区项目，与 Tesla 无隶属关系。
