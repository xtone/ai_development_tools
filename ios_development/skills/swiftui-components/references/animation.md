# アニメーションコンポーネント

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | 備考 |
|--------------|-----|--------|-------|------|
| symbolEffect | 17+ | 17+ | 14+ | SF Symbolsアニメーション |
| contentTransition | 17+ | 17+ | 14+ | コンテンツ変更アニメ |
| phaseAnimator | 17+ | 17+ | 14+ | 複数フェーズアニメ |
| keyframeAnimator | 17+ | 17+ | 14+ | キーフレームアニメ |
| sensoryFeedback | 17+ | 17+ | - | 触覚フィードバック |
| @Animatable | 26+ | 26+ | 26+ | アニメーション対応マクロ |

---

## symbolEffect (iOS 17+)

SF Symbolsに対してアニメーション効果を適用。

### バウンスエフェクト

```swift
@State private var notificationCount = 0

Image(systemName: "bell")
    .symbolEffect(.bounce, value: notificationCount)

Button("通知") {
    notificationCount += 1
}
```

### パルスエフェクト（繰り返し）

```swift
Image(systemName: "heart.fill")
    .symbolEffect(.pulse.wholeSymbol, options: .repeating)
```

### 可変カラー

```swift
Image(systemName: "wifi")
    .symbolEffect(.variableColor.iterative, options: .repeating)
```

### 制御付きアニメーション

```swift
@State private var isAnimating = false

Image(systemName: "arrow.down.circle")
    .symbolEffect(.bounce, options: .repeat(3), value: isAnimating)

Button("アニメーション開始") {
    isAnimating.toggle()
}
```

### 置換アニメーション

```swift
@State private var isPlaying = false

Image(systemName: isPlaying ? "pause.fill" : "play.fill")
    .contentTransition(.symbolEffect(.replace))

Button("切り替え") {
    withAnimation {
        isPlaying.toggle()
    }
}
```

---

## contentTransition (iOS 17+)

テキストやコンテンツの変更をアニメーション化。

### 数値のアニメーション

```swift
struct CounterView: View {
    @State private var count = 0

    var body: some View {
        Text("\(count)")
            .font(.largeTitle)
            .contentTransition(.numericText())

        Button("増加") {
            withAnimation {
                count += 1
            }
        }
    }
}
```

### 補間アニメーション

```swift
Text(status)
    .contentTransition(.interpolate) // 補間アニメーション
```

### シンボル置換

```swift
Image(systemName: isFavorite ? "star.fill" : "star")
    .contentTransition(.symbolEffect(.replace))
```

---

## phaseAnimator (iOS 17+)

複数フェーズのアニメーションを定義。

### 基本的な使用法

```swift
struct PulsingView: View {
    var body: some View {
        Circle()
            .fill(.blue)
            .phaseAnimator([false, true]) { content, phase in
                content
                    .scaleEffect(phase ? 1.2 : 1.0)
                    .opacity(phase ? 0.5 : 1.0)
            } animation: { phase in
                .easeInOut(duration: 0.5)
            }
    }
}
```

### カスタムフェーズ

```swift
enum AnimationPhase: CaseIterable {
    case initial, scaled, rotated, final
}

Circle()
    .phaseAnimator(AnimationPhase.allCases) { content, phase in
        content
            .scaleEffect(phase == .scaled ? 1.5 : 1.0)
            .rotationEffect(.degrees(phase == .rotated ? 180 : 0))
    } animation: { phase in
        switch phase {
        case .initial: .easeIn(duration: 0.3)
        case .scaled: .spring(duration: 0.5)
        case .rotated: .easeOut(duration: 0.4)
        case .final: .linear(duration: 0.2)
        }
    }
```

### トリガー付き

```swift
@State private var trigger = false

Circle()
    .phaseAnimator([0, 1, 2], trigger: trigger) { content, phase in
        content
            .scaleEffect(1.0 + Double(phase) * 0.1)
    }

Button("Animate") {
    trigger.toggle()
}
```

---

## keyframeAnimator (iOS 17+)

キーフレームベースの詳細なアニメーション制御。

### 基本的な使用法

```swift
struct BouncingView: View {
    @State private var trigger = false

    var body: some View {
        Circle()
            .keyframeAnimator(
                initialValue: AnimationValues(),
                trigger: trigger
            ) { content, value in
                content
                    .scaleEffect(value.scale)
                    .offset(y: value.verticalOffset)
            } keyframes: { _ in
                KeyframeTrack(\.scale) {
                    SpringKeyframe(1.2, duration: 0.2)
                    SpringKeyframe(1.0, duration: 0.2)
                }
                KeyframeTrack(\.verticalOffset) {
                    LinearKeyframe(-50, duration: 0.15)
                    SpringKeyframe(0, duration: 0.3)
                }
            }

        Button("Bounce") {
            trigger.toggle()
        }
    }
}

struct AnimationValues {
    var scale = 1.0
    var verticalOffset = 0.0
}
```

### 複雑なアニメーション

```swift
struct ComplexAnimationValues {
    var scale = 1.0
    var rotation = 0.0
    var opacity = 1.0
    var xOffset = 0.0
}

Rectangle()
    .keyframeAnimator(
        initialValue: ComplexAnimationValues(),
        trigger: trigger
    ) { content, value in
        content
            .scaleEffect(value.scale)
            .rotationEffect(.degrees(value.rotation))
            .opacity(value.opacity)
            .offset(x: value.xOffset)
    } keyframes: { _ in
        KeyframeTrack(\.scale) {
            CubicKeyframe(1.5, duration: 0.3)
            CubicKeyframe(1.0, duration: 0.3)
        }
        KeyframeTrack(\.rotation) {
            LinearKeyframe(360, duration: 0.6)
        }
        KeyframeTrack(\.opacity) {
            LinearKeyframe(0.5, duration: 0.3)
            LinearKeyframe(1.0, duration: 0.3)
        }
    }
```

---

## sensoryFeedback (iOS 17+)

触覚フィードバックの簡易化。`UIFeedbackGenerator`の代替。

### 基本的な使用法

```swift
struct InteractiveView: View {
    @State private var isSelected = false

    var body: some View {
        Button("選択") {
            isSelected.toggle()
        }
        .sensoryFeedback(.selection, trigger: isSelected)
    }
}
```

### 成功・エラーフィードバック

```swift
Button("送信") {
    submit()
}
.sensoryFeedback(.success, trigger: submitSucceeded)
.sensoryFeedback(.error, trigger: submitFailed)
```

### カスタム条件

```swift
.sensoryFeedback(trigger: errorOccurred) { oldValue, newValue in
    newValue ? .error : nil
}
```

### フィードバックタイプ

```swift
.sensoryFeedback(.impact)           // 衝撃
.sensoryFeedback(.selection)        // 選択
.sensoryFeedback(.success)          // 成功
.sensoryFeedback(.warning)          // 警告
.sensoryFeedback(.error)            // エラー
.sensoryFeedback(.increase)         // 増加
.sensoryFeedback(.decrease)         // 減少
```

---

## @Animatable マクロ (iOS 26+)

従来の `animatableData` ボイラープレートを削減するマクロ。

### Before (iOS 25以前)

```swift
struct LoadingArc: Shape {
    var center: CGPoint
    var radius: CGFloat
    var startAngle: Angle
    var endAngle: Angle
    var drawPathClockwise: Bool

    var animatableData: AnimatablePair<
        AnimatablePair<CGPoint.AnimatableData, CGFloat>,
        AnimatablePair<Angle.AnimatableData, Angle.AnimatableData>
    > {
        get {
            AnimatablePair(
                AnimatablePair(center.animatableData, radius),
                AnimatablePair(startAngle.animatableData, endAngle.animatableData)
            )
        }
        set {
            center.animatableData = newValue.first.first
            radius = newValue.first.second
            startAngle.animatableData = newValue.second.first
            endAngle.animatableData = newValue.second.second
        }
    }

    func path(in rect: CGRect) -> Path {
        // パス生成ロジック
    }
}
```

### After (iOS 26+)

```swift
import SwiftUI

@Animatable
struct LoadingArc: Shape {
    var center: CGPoint
    var radius: CGFloat
    var startAngle: Angle
    var endAngle: Angle

    @AnimatableIgnored
    var drawPathClockwise: Bool

    func path(in rect: CGRect) -> Path {
        // パス生成ロジック
        Path()
    }
}
```

### @AnimatableIgnored

アニメーション対象から除外するプロパティに使用。

```swift
@Animatable
struct CustomShape: Shape {
    var animatedValue: CGFloat      // アニメーション対象

    @AnimatableIgnored
    var staticConfig: Configuration // アニメーション対象外

    func path(in rect: CGRect) -> Path {
        // ...
    }
}
```

---

## 関連ドキュメント

- [symbolEffect - Apple Developer](https://developer.apple.com/documentation/swiftui/view/symboleffect(_:options:isactive:))
- [ContentTransition - Apple Developer](https://developer.apple.com/documentation/swiftui/contenttransition)
- [phaseAnimator - Apple Developer](https://developer.apple.com/documentation/swiftui/view/phaseanimator(_:content:animation:))
- [keyframeAnimator - Apple Developer](https://developer.apple.com/documentation/swiftui/view/keyframeanimator(initialvalue:repeating:content:keyframes:))
