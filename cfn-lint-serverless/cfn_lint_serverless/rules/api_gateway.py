"""
Rules for API Gateway resources
"""


import json
import re

from cfnlint.rules import CloudFormationLintRule, RuleMatch


class ApiGatewayLoggingRule(CloudFormationLintRule):
    """
    Ensure API Gateway REST and HTTP APIs have logging enabled
    """

    id = "ES2000"  # noqa: VNE003
    shortdesc = "API Gateway Logging"
    description = "Ensure that API Gateway REST and HTTP APIs have logging enabled"
    tags = ["apigateway"]

    _message_access_log_settings = "API Gateway stage {} is missing the AccessLogSetting property."
    _message_destination_arn = "API Gateway stage {} is missing the AccessLogSetting.DestinationArn property."

    def match(self, cfn):
        """
        Match against API Gateway stages without log settings
        """

        matches = []

        for key, value in cfn.get_resources(["AWS::ApiGateway::Stage", "AWS::ApiGatewayV2::Stage"]).items():
            if value["Type"] == "AWS::ApiGateway::Stage":
                # REST APIs
                log_settings = value.get("Properties", {}).get("AccessLogSetting", None)
            else:
                # HTTP APIs
                log_settings = value.get("Properties", {}).get("AccessLogSettings", None)

            if log_settings is None:
                matches.append(
                    RuleMatch(
                        ["Resources", key],
                        self._message_access_log_settings.format(key),
                    )
                )
            elif log_settings.get("DestinationArn", None) is None:
                matches.append(RuleMatch(["Resources", key], self._message_destination_arn.format(key)))

        return matches


class ApiGatewayStructuredLoggingRule(CloudFormationLintRule):
    """
    Ensure API Gateway REST and HTTP APIs use structured logging
    """

    id = "WS2001"  # noqa: VNE003
    shortdesc = "API Gateway Structured Logging"
    description = "Ensure that API Gateway REST and HTTP APIs are using structured logs"
    tags = ["apigateway"]

    _message = "API Gateway stage {} is not using structured logging for the AccessLogSetting.Format property."
    _log_format_pattern = re.compile(r"\$context\.[a-zA-Z\.]+")

    def _check_log_format(self, log_format: str) -> bool:
        """
        Validate if a log Format is valid JSON

        As users can use non-string keys like '$context.integration.latency', we
        need to transform the log format into something that can be decoded into
        JSON first.
        """

        log_format = self._log_format_pattern.sub("0", log_format)

        try:
            json.loads(log_format)
            return True
        except json.decoder.JSONDecodeError:
            return False

    def match(self, cfn):
        """
        Match against API Gateway stages not using structured logging
        """

        matches = []

        for key, value in cfn.get_resources(["AWS::ApiGateway::Stage", "AWS::ApiGatewayV2::Stage"]).items():
            if value["Type"] == "AWS::ApiGateway::Stage":
                # REST APIs
                log_format = value.get("Properties", {}).get("AccessLogSetting", {}).get("Format", None)
            else:
                # HTTPI APIs
                log_format = value.get("Properties", {}).get("AccessLogSettings", {}).get("Format", None)

            # Ignore if it's not set. Another rule should catch it.
            if log_format is None:
                continue

            if not self._check_log_format(log_format):
                matches.append(RuleMatch(["Resources", key], self._message.format(key)))

        return matches


class ApiGatewayDefaultThrottlingRule(CloudFormationLintRule):
    """
    Ensure API Gateway REST APIs have throttling enabled
    """

    id = "ES2003"  # noqa: VNE003
    shortdesc = "API Gateway Throttling"
    description = "Ensure that API Gateway REST APIs have default throttling limits set."
    tags = ["apigateway"]

    _message_method_settings = "API Gateway stage {} does not have a default MethodSettings property with ThrottlingBurstLimit and ThrottlingRateLimit."
    _message_default_route_settings = "API Gateway stage {} does not have a default DefaultRouteSettings property with ThrottlingBurstLimit and ThrottlingRateLimit."

    def match(self, cfn):
        """
        Match against API Gateway stages without default throttling
        """

        matches = []

        # API Gateway REST APIs
        for key, value in cfn.get_resources(["AWS::ApiGateway::Stage"]).items():
            print("HI")
            method_settings = [
                ms
                for ms in value.get("Properties", {}).get("MethodSettings", [])
                if ms.get("HttpMethod") == "*" and ms.get("ResourcePath") == "/*"
            ] or [{}]
            default_method_setting = method_settings[0]

            print(default_method_setting)

            if (
                "ThrottlingBurstLimit" not in default_method_setting
                or "ThrottlingRateLimit" not in default_method_setting
            ):
                matches.append(RuleMatch(["Resources", key], self._message_method_settings.format(key)))

        # API Gateway HTTP APIs
        for key, value in cfn.get_resources(["AWS::ApiGatewayV2::Stage"]).items():
            route_settings = value.get("Properties", {}).get("DefaultRouteSettings", {})

            if "ThrottlingBurstLimit" not in route_settings or "ThrottlingRateLimit" not in route_settings:
                matches.append(RuleMatch(["Resources", key], self._message_default_route_settings.format(key)))

        return matches


class ApiGatewayTracingRule(CloudFormationLintRule):
    """
    Ensure API Gateway REST APIs have tracing enabled
    """

    id = "ES2002"  # noqa: VNE003
    shortdesc = "API Gateway Tracing"
    description = "Ensure that API Gateway REST APIs have tracing enabled"
    tags = ["apigateway"]

    _message = "API Gateway stage {} does not have the TracingEnabled property set to true."

    def match(self, cfn):
        """
        Match against API Gateway stages without tracing enabled
        """

        matches = []

        # HTTP APIs don't support X-Ray
        # for key, value in cfn.get_resources(["AWS::ApiGateway::Stage", "AWS::ApiGatewayV2::Stage"]).items():
        for key, value in cfn.get_resources(["AWS::ApiGateway::Stage"]).items():
            tracing_enabled = value.get("Properties", {}).get("TracingEnabled", False)

            if not tracing_enabled:
                matches.append(RuleMatch(["Resources", key], self._message.format(key)))

        return matches
