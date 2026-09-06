import SwiftUI
import AicodeXCore

struct ActionsView: View {
    @EnvironmentObject private var model: AppViewModel

    var body: some View {
        NavigationStack {
            List(QuickAction.defaults) { action in
                Button {
                    model.run(action)
                } label: {
                    Label(action.title, systemImage: action.systemImage)
                }
            }
            .navigationTitle("Actions")
        }
    }
}
