# チャート・グラフコンポーネント

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | 備考 |
|--------------|-----|--------|-------|------|
| Swift Charts | 16+ | 16+ | 13+ | 宣言的チャートフレームワーク |
| LineMark | 16+ | 16+ | 13+ | 折れ線グラフ |
| BarMark | 16+ | 16+ | 13+ | 棒グラフ |
| AreaMark | 16+ | 16+ | 13+ | 面グラフ |
| PointMark | 16+ | 16+ | 13+ | 散布図 |
| RectangleMark | 16+ | 16+ | 13+ | 矩形マーク |
| RuleMark | 16+ | 16+ | 13+ | 線（軸線・参照線） |
| Chart3D | 26+ | 26+ | - | 3Dチャート |

---

## Swift Charts (iOS 16+)

iOS 16で導入された宣言的なチャートフレームワーク。

### 基本的な折れ線グラフ

```swift
import Charts

struct SalesData: Identifiable {
    let id = UUID()
    let month: String
    let sales: Int
}

struct SalesChart: View {
    let data: [SalesData]

    var body: some View {
        Chart(data) { item in
            LineMark(
                x: .value("月", item.month),
                y: .value("売上", item.sales)
            )
        }
    }
}
```

### 棒グラフ

```swift
Chart(data) { item in
    BarMark(
        x: .value("カテゴリ", item.category),
        y: .value("値", item.value)
    )
    .foregroundStyle(by: .value("タイプ", item.type))
}
```

### 面グラフ

```swift
Chart(data) { item in
    AreaMark(
        x: .value("日付", item.date),
        y: .value("値", item.value)
    )
    .foregroundStyle(.blue.opacity(0.3))
}
```

### 散布図

```swift
Chart(data) { item in
    PointMark(
        x: .value("X", item.x),
        y: .value("Y", item.y)
    )
    .symbolSize(item.size)
}
```

### カスタマイズ

```swift
Chart(data) { item in
    LineMark(
        x: .value("日付", item.date),
        y: .value("値", item.value)
    )
    .interpolationMethod(.catmullRom) // 曲線補間
    .symbol(Circle())
    .foregroundStyle(.blue)
}
.chartXAxis {
    AxisMarks(values: .stride(by: .month)) { value in
        AxisValueLabel(format: .dateTime.month(.abbreviated))
    }
}
.chartYAxis {
    AxisMarks(position: .leading)
}
.chartLegend(position: .bottom)
```

### 複合チャート

```swift
Chart {
    ForEach(salesData) { item in
        BarMark(
            x: .value("月", item.month),
            y: .value("売上", item.sales)
        )
        .foregroundStyle(.blue.opacity(0.5))
    }

    ForEach(targetData) { item in
        LineMark(
            x: .value("月", item.month),
            y: .value("目標", item.target)
        )
        .foregroundStyle(.red)
        .lineStyle(StrokeStyle(lineWidth: 2, dash: [5, 3]))
    }

    RuleMark(y: .value("平均", averageValue))
        .foregroundStyle(.green)
        .annotation(position: .trailing) {
            Text("平均")
                .font(.caption)
        }
}
```

### インタラクティブなチャート

```swift
struct InteractiveChart: View {
    @State private var selectedElement: SalesData?

    var body: some View {
        Chart(data) { item in
            BarMark(
                x: .value("月", item.month),
                y: .value("売上", item.sales)
            )
            .opacity(selectedElement == nil || selectedElement?.id == item.id ? 1 : 0.3)
        }
        .chartOverlay { proxy in
            GeometryReader { geometry in
                Rectangle()
                    .fill(.clear)
                    .contentShape(Rectangle())
                    .gesture(
                        DragGesture(minimumDistance: 0)
                            .onChanged { value in
                                let location = value.location
                                if let month: String = proxy.value(atX: location.x) {
                                    selectedElement = data.first { $0.month == month }
                                }
                            }
                            .onEnded { _ in
                                selectedElement = nil
                            }
                    )
            }
        }
    }
}
```

---

## Chart3D (iOS 26+)

iOS 26で導入された3Dチャートのネイティブサポート。

### 基本的な使用法

```swift
import Charts

Chart3D {
    // PointMark, RuleMark, RectangleMark, SurfacePlot
}
```

### 3D散布図

```swift
Chart3D(data) { item in
    PointMark(
        x: .value("X", item.x),
        y: .value("Y", item.y),
        z: .value("Z", item.z)
    )
}
```

> **注意**: Chart3Dは現在iPadOSとmacOSでは利用できません。

---

## 移行チェックリスト

### Chart導入

1. [ ] `import Charts`を追加
2. [ ] データモデルを`Identifiable`に準拠
3. [ ] 適切なMark（LineMark, BarMark等）を選択
4. [ ] 軸とレジェンドをカスタマイズ

---

## 関連ドキュメント

- [Swift Charts - Apple Developer](https://developer.apple.com/documentation/charts)
- [Creating a chart using Swift Charts - Apple Developer](https://developer.apple.com/documentation/charts/creating-a-chart-using-swift-charts)
