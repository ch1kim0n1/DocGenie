from __future__ import annotations

from pathlib import Path

from docgenie.generator import ReadmeGenerator


def _base() -> dict:
    return {
        "project_name": "Proj",
        "files_analyzed": 3,
        "languages": {"python": 2, "javascript": 1},
        "main_language": "python",
        "dependencies": {},
        "project_structure": {"root": {"files": [], "dirs": []}},
        "functions": [],
        "classes": [],
        "imports": {},
        "documentation_files": [],
        "config_files": [],
        "git_info": {},
        "is_website": False,
        "website_detection_reason": "",
    }


def test_get_project_name_fallbacks() -> None:
    gen = ReadmeGenerator()
    assert gen._get_project_name({"project_name": "X"}) == "X"
    assert gen._get_project_name({"git_info": {"repo_name": "org/repo"}}) == "repo"
    assert gen._get_project_name({"git_info": {"repo_name": "repo"}}) == "repo"
    assert gen._get_project_name({"root_path": "/tmp/myproj"}) == "myproj"
    assert gen._get_project_name({}) == "Project"


def test_generate_description_website_and_nonwebsite() -> None:
    gen = ReadmeGenerator()
    website = _base()
    website["project_structure"]["root"]["files"] = ["index.html"]
    website["dependencies"] = {"package.json": ["react", "shop"]}
    assert "e-commerce website" in gen._generate_description(website)

    website["dependencies"] = {"package.json": ["blog", "vue"]}
    assert "blog/content management website" in gen._generate_description(website)

    website["dependencies"] = {"package.json": ["portfolio", "angular"]}
    assert "portfolio website" in gen._generate_description(website)

    website["dependencies"] = {"package.json": ["dashboard", "gatsby"]}
    assert "web dashboard application" in gen._generate_description(website)

    website["dependencies"] = {"package.json": ["doc", "next"]}
    assert "documentation website" in gen._generate_description(website)

    website["dependencies"] = {"package.json": ["plain"]}
    assert "modern web application" in gen._generate_description(website)

    app = _base()
    app["dependencies"] = {"requirements.txt": ["httpx", "server"]}
    assert "web application" in gen._generate_description(app)
    app["dependencies"] = {"requirements.txt": ["rest"]}
    assert "API service" in gen._generate_description(app)
    app["dependencies"] = {"requirements.txt": ["command"]}
    assert "command-line tool" in gen._generate_description(app)
    app["dependencies"] = {"requirements.txt": ["analysis"]}
    assert "data analysis tool" in gen._generate_description(app)
    app["dependencies"] = {"requirements.txt": ["game"]}
    assert "game" in gen._generate_description(app)
    app["dependencies"] = {"requirements.txt": ["none"]}
    assert "application" in gen._generate_description(app)


def test_install_commands_and_usage_examples() -> None:
    gen = ReadmeGenerator()
    analysis = _base()
    analysis["project_structure"]["root"]["files"] = [
        "requirements.txt",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
    ]
    cmds = gen._generate_install_commands(analysis)
    text = "\n".join(c["command"] for c in cmds)
    assert "pip install -r requirements.txt" in text
    assert "npm install" in text
    assert "cargo build" in text
    assert "go mod download" in text
    assert "mvn clean install" in text

    analysis2 = _base()
    analysis2["project_structure"]["root"]["files"] = ["pyproject.toml", "build.gradle"]
    cmds2 = gen._generate_install_commands(analysis2)
    text2 = "\n".join(c["command"] for c in cmds2)
    assert "poetry install" in text2
    assert "./gradlew build" in text2

    analysis3 = _base()
    analysis3["project_structure"]["root"]["files"] = ["setup.py"]
    assert any("pip install -e ." in c["command"] for c in gen._generate_install_commands(analysis3))

    py = _base()
    py["functions"] = [{"name": "main"}]
    assert gen._generate_usage_examples(py)[0]["command"] == "python main.py"

    py2 = _base()
    py2["classes"] = [{"name": "Runner"}]
    assert "Runner" in gen._generate_usage_examples(py2)[0]["command"]

    js = _base()
    js["main_language"] = "javascript"
    assert len(gen._generate_usage_examples(js)) == 2

    java = _base()
    java["main_language"] = "java"
    assert "java -jar" in gen._generate_usage_examples(java)[0]["command"]

    rust = _base()
    rust["main_language"] = "rust"
    assert "cargo run" in gen._generate_usage_examples(rust)[0]["command"]

    go = _base()
    go["main_language"] = "go"
    assert "go run" in gen._generate_usage_examples(go)[0]["command"]

    unknown = _base()
    unknown["main_language"] = "unknown"
    assert "Basic usage" in gen._generate_usage_examples(unknown)[0]["title"]


def test_api_docs_features_requirements_and_tests_detection() -> None:
    gen = ReadmeGenerator()
    funcs = [{"name": "public", "file": "a.py", "line": 1}, {"name": "_private"}]
    classes = [{"name": "A", "methods": [{"name": "m"}]}, {"name": "_Hidden"}]
    api = gen._generate_api_docs(funcs, classes, {"template_customizations": {"max_functions_documented": 1}})
    assert [f["name"] for f in api["functions"]] == ["public"]
    assert [c["name"] for c in api["classes"]] == ["A"]

    analysis = _base()
    analysis["dependencies"] = {
        "requirements.txt": ["web", "api", "database", "test", "auth", "redis"],
    }
    analysis["functions"] = [{"name": "async_task", "is_async": True}]
    analysis["classes"] = [{"name": str(i)} for i in range(6)]
    analysis["git_info"] = {"contributor_count": 2}
    features = gen._extract_features(analysis)
    assert len(features) >= 8

    assert gen._extract_features(_base()) == [
        "High performance",
        "Easy to use",
        "Modular design",
        "Configurable",
    ]

    reqs = gen._extract_requirements(
        {"package.json": {}, "requirements.txt": [], "Cargo.toml": {}, "go.mod": {}, "pom.xml": {}}
    )
    assert "Node.js 14.0 or higher" in reqs
    assert "Python 3.8 or higher" in reqs
    assert "Rust 1.60 or higher" in reqs
    assert "Go 1.18 or higher" in reqs
    assert "Java 11 or higher" in reqs
    assert gen._extract_requirements({}) == ["See installation instructions below"]

    assert gen._has_tests({"project_structure": {"tests": {}, "root": {"files": [], "dirs": []}}})
    assert gen._has_tests({"project_structure": {"root": {"files": ["test_app.py"], "dirs": []}}})
    assert gen._has_tests({"project_structure": {"root": {"files": ["app_test.py"], "dirs": []}}})
    assert not gen._has_tests({"project_structure": {"root": {"files": ["app.py"], "dirs": []}}})


def test_get_website_info_and_helpers() -> None:
    gen = ReadmeGenerator()
    analysis = _base()
    analysis["project_structure"] = {
        "root": {
            "files": [
                "index.html",
                "webpack.config.js",
                "_config.yml",
                "netlify.toml",
                "vercel.json",
                "firebase.json",
                "Dockerfile",
            ],
            "dirs": [],
        },
        "public/assets": {"files": [], "dirs": []},
        ".github/workflows": {"files": [], "dirs": []},
    }
    analysis["dependencies"] = {"package.json": ["react", "bootstrap"]}
    info = gen._get_website_info(analysis)
    assert info["entry_points"] == ["index.html"]
    assert info["build_system"] == "Webpack"
    assert info["static_site_generator"] == "Jekyll"
    assert "public/assets" in info["asset_directories"]
    assert set(info["deployment_platforms"]) == {
        "GitHub Actions",
        "Netlify",
        "Vercel",
        "Firebase",
        "Docker",
    }
    assert info["has_responsive_design"] is True
    assert info["framework_detected"] == "React"

    # Cover alternative branch variants.
    for file_name, expected in [
        ("vite.config.js", "Vite"),
        ("rollup.config.js", "Rollup"),
        ("parcel.json", "Parcel"),
        ("gatsby-config.js", "Gatsby"),
        ("next.config.js", "Next.js"),
    ]:
        alt = _base()
        alt["project_structure"]["root"]["files"] = [file_name]
        assert gen._get_website_info(alt)["build_system"] == expected

    for file_name, expected in [
        ("hugo.toml", "Hugo"),
        ("mkdocs.yml", "MkDocs"),
        ("docusaurus.config.js", "Docusaurus"),
    ]:
        alt = _base()
        alt["project_structure"]["root"]["files"] = [file_name]
        assert gen._get_website_info(alt)["static_site_generator"] == expected

    assert gen._detect_frontend_framework({"package.json": ["vue"]}) == "Vue.js"
    assert gen._detect_frontend_framework({"package.json": ["angular"]}) == "Angular"
    assert gen._detect_frontend_framework({"package.json": ["svelte"]}) == "Svelte"
    assert gen._detect_frontend_framework({"package.json": ["ember"]}) == "Ember.js"
    assert gen._detect_frontend_framework({"package.json": ["backbone"]}) == "Backbone.js"
    assert gen._detect_frontend_framework({"package.json": ["jquery"]}) == "jQuery"
    assert gen._detect_frontend_framework({"package.json": ["none"]}) is None
    assert gen._check_responsive_design({"dependencies": {"package.json": ["tailwind"]}})


def test_prepare_context_non_dict_config_and_generate_output(tmp_path: Path) -> None:
    gen = ReadmeGenerator()
    analysis = _base()
    analysis["config"] = "not-a-dict"
    analysis["dependencies"] = {"requirements.txt": ["requests"]}
    analysis["functions"] = [{"name": "public", "file": "a.py", "line": 1, "docstring": "d", "args": []}]
    analysis["classes"] = [{"name": "C", "file": "a.py", "line": 2, "docstring": "", "methods": []}]

    content = gen.generate(analysis, str(tmp_path / "README.md"))
    assert "Proj" in content
    assert (tmp_path / "README.md").exists()

    website = _base()
    website["project_structure"]["root"]["files"] = ["index.html"]
    website["dependencies"] = {"package.json": ["react"]}
    gen.generate(website, str(tmp_path / "README-website.md"))
    assert (tmp_path / "README-website.md").exists()


def test_quality_report_and_template_section() -> None:
    gen = ReadmeGenerator()
    analysis = _base()
    analysis["files_analyzed"] = 25
    analysis["languages"] = {"python": 10, "javascript": 3}
    analysis["functions"] = [{"name": f"f{i}"} for i in range(8)]
    analysis["classes"] = [{"name": f"C{i}"} for i in range(3)]
    analysis["dependencies"] = {"requirements.txt": ["requests"]}
    analysis["project_structure"] = {"root": {"files": ["README.md"], "dirs": []}, "tests": {}}

    quality = gen._build_quality_report(analysis)
    assert quality["score"] >= 75
    assert quality["confidence"] == "High"

    content = gen.generate(analysis)
    assert "Documentation Quality" in content
    assert "Quality Score" in content
    assert "Confidence" in content


def test_generator_redaction_and_package_docs(tmp_path: Path) -> None:
    gen = ReadmeGenerator()
    analysis = _base()
    analysis["config"] = {"safety": {"redaction_mode": "strict"}}
    analysis["project_name"] = "token=abcdef12345678"
    out = gen.generate(analysis)
    assert "[REDACTED]" in out

    analysis2 = _base()
    analysis2["root_path"] = str(tmp_path)
    analysis2["packages"] = [{"path": "pkg-a"}, {"path": "."}]
    abs_pkg = tmp_path / "pkg-a"
    abs_pkg.mkdir(parents=True, exist_ok=True)
    analysis2["functions"] = [{"name": "f", "file": str(abs_pkg / "main.py")}]
    analysis2["classes"] = []
    artifacts = gen.generate_package_docs(analysis2, tmp_path / ".docgenie" / "packages")
    assert "pkg-a" in artifacts
    assert (tmp_path / ".docgenie" / "packages" / "pkg-a" / "README.md").exists()
