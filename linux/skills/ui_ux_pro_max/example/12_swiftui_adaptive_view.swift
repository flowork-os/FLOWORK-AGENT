import SwiftUI

struct SovereignTelemetryView: View {
    @State private var isRunning: Bool = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Engine Node Diagnostics")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.primary)

            HStack {
                Circle()
                    .fill(isRunning ? Color.green : Color.orange)
                    .frame(width: 10, height: 10)
                Text(isRunning ? "Active" : "Standby")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            Button(action: { isRunning.toggle() }) {
                Text(isRunning ? "Halt Worker" : "Engage Worker")
                    .frame(minWidth: 120, minHeight: 32)
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(24)
        .background(Color(NSColor.windowBackgroundColor))
        .cornerRadius(10)
    }
}
