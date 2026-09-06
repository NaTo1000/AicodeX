import SwiftUI
import AicodeXCore

struct SnippetsView: View {
    @EnvironmentObject private var model: AppViewModel

    var body: some View {
        NavigationStack {
            List(model.filteredSnippets) { snippet in
                NavigationLink(value: snippet) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(snippet.name).font(.headline)
                        Text(snippet.language)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Snippets")
            .searchable(text: $model.searchText, prompt: "Search snippets")
            .navigationDestination(for: Snippet.self) { snippet in
                SnippetDetailView(snippet: snippet)
            }
            .overlay {
                if model.filteredSnippets.isEmpty {
                    ContentUnavailableView(
                        "No Snippets",
                        systemImage: "doc.text.magnifyingglass",
                        description: Text("Try a different search.")
                    )
                }
            }
        }
    }
}

struct SnippetDetailView: View {
    @EnvironmentObject private var model: AppViewModel
    let snippet: Snippet

    var body: some View {
        ScrollView {
            Text(snippet.code)
                .font(.system(.body, design: .monospaced))
                .textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
        }
        .navigationTitle(snippet.name)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    model.insertSnippet(snippet)
                } label: {
                    Label("Copy", systemImage: "doc.on.doc")
                }
            }
        }
    }
}
