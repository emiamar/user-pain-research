import Foundation
import SwiftData

@Model
final class CheckIn {
    var date: Date
    init(date: Date) { self.date = date }
}

@Model
final class Habit {
    var name: String
    var reminderTime: Date?
    @Relationship(deleteRule: .cascade) var checkIns: [CheckIn] = []

    init(name: String) { self.name = name }

    /// Consecutive days with a check-in, counting back from today.
    /// One missed day resets the streak to 0. There are no skip days,
    /// rest days or "freeze" options.
    var currentStreak: Int {
        let cal = Calendar.current
        var day = cal.startOfDay(for: .now)
        let days = Set(checkIns.map { cal.startOfDay(for: $0.date) })
        var streak = 0
        while days.contains(day) {
            streak += 1
            day = cal.date(byAdding: .day, value: -1, to: day)!
        }
        return streak
    }
}

/// Storage is local-only (on-device SwiftData store). No iCloud or other sync.
@MainActor
final class HabitStore {
    let container: ModelContainer
    init() throws {
        container = try ModelContainer(for: Habit.self, CheckIn.self)
    }
}
