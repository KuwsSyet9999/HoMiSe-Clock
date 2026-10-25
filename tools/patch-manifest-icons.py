"""Patch AndroidManifest.xml so every icon variant has its own launcher alias.

Android can only switch the launcher icon by enabling one <activity-alias> and
disabling the rest, so all 192 variants (48 faces x 2 schemes x 2 ghost states) must be declared statically.

Actions:
  * give <application> a default icon (variant 0) as a fallback;
  * strip the launcher <intent-filter> from MainActivity -- the aliases own the
    launcher entry now, and leaving it would create a second, unfollowable icon;
  * append one <activity-alias> per variant, only variant 0 enabled initially.

IMPORTANT -- alias names use ${applicationId}, not a literal or a relative name:
PackageManager refuses to touch a component whose package prefix differs from the
app's own package name ("not a component of this package"), so an alias resolved
against the *namespace* breaks on any build with an applicationIdSuffix (e.g. the
.debug variant): getComponentEnabledSetting throws and the icon never switches.
${applicationId} expands to the final id after the suffix is applied.
"""
import os
import re

ROOT = r"D:\DSHin\HoMiSe"
MANIFEST = os.path.join(ROOT, "app", "src", "main", "AndroidManifest.xml")
VARIANTS = os.path.join(ROOT, "docs", "icon", "variants.txt")
PKG = "com.homise.clock"
COUNT = 192

ALIAS = """        <activity-alias
            android:name="${{applicationId}}.icon.IconV{i}"
            android:enabled="{enabled}"
            android:exported="true"
            android:icon="@mipmap/ic_v{i}"
            android:label="@string/app_name"
            android:targetActivity=".MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>
"""


def main():
    with open(MANIFEST, "r", encoding="utf-8") as f:
        text = f.read()

    # Idempotent: drop any previously injected aliases before re-adding.
    text = re.sub(r"\n *<activity-alias.*?</activity-alias>", "", text, flags=re.S)

    # The application icon is only a fallback; every real entry point is an alias.
    text = text.replace(
        'android:icon="@mipmap/ic_launcher"\n        android:roundIcon="@mipmap/ic_launcher_round"',
        'android:icon="@mipmap/ic_v0"\n        android:roundIcon="@mipmap/ic_v0"',
    )

    # MainActivity keeps exported=true (so `am start -n` still works) but loses the
    # launcher filter, which now belongs to the aliases.
    text = re.sub(
        r"(<activity\b[^>]*?\bandroid:name=\"\.MainActivity\"[^>]*?>)\s*"
        r"<intent-filter>.*?</intent-filter>\s*(</activity>)",
        r"\1\2",
        text,
        flags=re.S,
    )
    # Collapse the self-closing form for tidiness.
    text = text.replace(">\n        </activity>", " />")

    aliases = "\n" + "".join(
        ALIAS.format(i=i, enabled="true" if i == 0 else "false") for i in range(COUNT)
    )
    text = text.replace("    </application>", aliases + "    </application>")

    with open(MANIFEST, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"patched {MANIFEST}")
    print(f"  aliases added : {COUNT} (variant 0 enabled)")
    print(f"  package       : {PKG}")


if __name__ == "__main__":
    main()
