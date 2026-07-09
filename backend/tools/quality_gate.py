from quality_checks import check_class_methods, check_dependencies, check_file_size, check_functions, check_hardcoded
from quality_config import code_files, config_path, read_limits, read_list


def main() -> int:
    path = config_path()
    limits = read_limits(path)
    issues = collect_issues(read_list(path, "source_roots"), read_list(path, "hardcoded_markers"), limits)
    if issues:
        print("\n".join(issues))
        return 1
    print("quality_gate=pass")
    return 0


def collect_issues(roots: list[str], markers: list[str], limits: dict[str, int]) -> list[str]:
    issues = check_dependencies(limits["max_dependencies"])
    for file_path in code_files(roots):
        issues += check_file_size(file_path, limits["max_file_lines"])
        issues += check_hardcoded(file_path, markers)
        issues += check_functions(file_path, limits["max_function_lines"])
        issues += check_class_methods(file_path, limits["max_public_methods"])
    return issues


if __name__ == "__main__":
    raise SystemExit(main())
