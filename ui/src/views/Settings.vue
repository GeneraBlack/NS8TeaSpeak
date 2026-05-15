<!--
  Copyright (C) 2023 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("settings.title") }}</h2>
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getConfiguration">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-configuration')"
          :description="error.getConfiguration"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <cv-form @submit.prevent="configureModule">
            <cv-text-input
              :label="$t('settings.timezone')"
              v-model="timezone"
              :placeholder="$t('settings.timezone_placeholder')"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.timezone"
              ref="timezone"
            ></cv-text-input>
            <cv-text-input
              :label="$t('settings.license_key')"
              v-model="licenseKey"
              :placeholder="$t('settings.license_key_placeholder')"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.licenseKey"
              ref="licenseKey"
            ></cv-text-input>
            <cv-select
              :label="$t('settings.query_ssl_mode')"
              v-model="querySslMode"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.querySslMode"
              ref="querySslMode"
            >
              <cv-select-option value="0">{{
                $t("settings.query_ssl_disabled")
              }}</cv-select-option>
              <cv-select-option value="1">{{
                $t("settings.query_ssl_enforced")
              }}</cv-select-option>
              <cv-select-option value="2">{{
                $t("settings.query_ssl_hybrid")
              }}</cv-select-option>
            </cv-select>
            <cv-select
              :label="$t('settings.web_enabled')"
              v-model="webEnabled"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.webEnabled"
              ref="webEnabled"
            >
              <cv-select-option value="1">{{
                $t("settings.option_enabled")
              }}</cv-select-option>
              <cv-select-option value="0">{{
                $t("settings.option_disabled")
              }}</cv-select-option>
            </cv-select>
            <cv-text-input
              v-if="webEnabled === '1'"
              :label="$t('settings.web_host')"
              v-model="webHost"
              :placeholder="$t('settings.web_host_placeholder')"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.webHost"
              ref="webHost"
            ></cv-text-input>
            <cv-select
              v-if="webEnabled === '1'"
              :label="$t('settings.web_lets_encrypt')"
              v-model="webLetsEncrypt"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.webLetsEncrypt"
              ref="webLetsEncrypt"
            >
              <cv-select-option value="1">{{
                $t("settings.option_enabled")
              }}</cv-select-option>
              <cv-select-option value="0">{{
                $t("settings.option_disabled")
              }}</cv-select-option>
            </cv-select>
            <cv-select
              :label="$t('settings.music_enabled')"
              v-model="musicEnabled"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.musicEnabled"
              ref="musicEnabled"
            >
              <cv-select-option value="1">{{
                $t("settings.option_enabled")
              }}</cv-select-option>
              <cv-select-option value="0">{{
                $t("settings.option_disabled")
              }}</cv-select-option>
            </cv-select>
            <cv-select
              :label="$t('settings.vpn_check_enabled')"
              v-model="vpnCheckEnabled"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.vpnCheckEnabled"
              ref="vpnCheckEnabled"
            >
              <cv-select-option value="1">{{
                $t("settings.option_enabled")
              }}</cv-select-option>
              <cv-select-option value="0">{{
                $t("settings.option_disabled")
              }}</cv-select-option>
            </cv-select>
            <cv-row v-if="error.configureModule">
              <cv-column>
                <NsInlineNotification
                  kind="error"
                  :title="$t('action.configure-module')"
                  :description="error.configureModule"
                  :showCloseButton="false"
                />
              </cv-column>
            </cv-row>
            <NsButton
              kind="primary"
              :icon="Save20"
              :loading="loading.configureModule"
              :disabled="loading.getConfiguration || loading.configureModule"
              >{{ $t("settings.save") }}</NsButton
            >
          </cv-form>
        </cv-tile>
      </cv-column>
    </cv-row>
  </cv-grid>
</template>

<script>
import to from "await-to-js";
import { mapState } from "vuex";
import {
  QueryParamService,
  UtilService,
  TaskService,
  IconService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";

export default {
  name: "Settings",
  mixins: [
    TaskService,
    IconService,
    UtilService,
    QueryParamService,
    PageTitleService,
  ],
  pageTitle() {
    return this.$t("settings.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "settings",
      },
      urlCheckInterval: null,
      timezone: "UTC",
      licenseKey: "",
      querySslMode: "2",
      webEnabled: "1",
      webHost: "",
      webLetsEncrypt: "0",
      musicEnabled: "0",
      vpnCheckEnabled: "0",
      loading: {
        getConfiguration: false,
        configureModule: false,
      },
      error: {
        getConfiguration: "",
        configureModule: "",
        timezone: "",
        licenseKey: "",
        querySslMode: "",
        webEnabled: "",
        webHost: "",
        webLetsEncrypt: "",
        musicEnabled: "",
        vpnCheckEnabled: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.watchQueryData(vm);
      vm.urlCheckInterval = vm.initUrlBindingForApp(vm, vm.q.page);
    });
  },
  beforeRouteLeave(to, from, next) {
    clearInterval(this.urlCheckInterval);
    next();
  },
  created() {
    this.getConfiguration();
  },
  methods: {
    async getConfiguration() {
      this.loading.getConfiguration = true;
      this.error.getConfiguration = "";
      const taskAction = "get-configuration";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.getConfigurationAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.getConfigurationCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          extra: {
            title: this.$t("action." + taskAction),
            isNotificationHidden: true,
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.getConfiguration = this.getErrorMessage(err);
        this.loading.getConfiguration = false;
      }
    },
    getConfigurationAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.getConfiguration = this.$t("error.generic_error");
      this.loading.getConfiguration = false;
    },
    getConfigurationCompleted(taskContext, taskResult) {
      this.loading.getConfiguration = false;
      const config = taskResult.output;

      this.timezone = config.timezone || "UTC";
      this.licenseKey = config.license_key || "";
      this.querySslMode = String(config.query_ssl_mode ?? 2);
      this.webEnabled = this.booleanToSelectValue(config.web_enabled, true);
      this.webHost = config.web_host || "";
      this.webLetsEncrypt = this.booleanToSelectValue(
        config.web_lets_encrypt,
        false
      );
      this.musicEnabled = this.booleanToSelectValue(
        config.music_enabled,
        false
      );
      this.vpnCheckEnabled = this.booleanToSelectValue(
        config.vpn_check_enabled,
        false
      );

      this.focusElement("timezone");
    },
    validateConfigureModule() {
      this.clearErrors(this);
      let isValidationOk = true;

      if (!this.timezone) {
        this.error.timezone = this.$t("common.required");

        if (isValidationOk) {
          this.focusElement("timezone");
          isValidationOk = false;
        }
      }

      if (!["0", "1", "2"].includes(this.querySslMode)) {
        this.error.querySslMode = this.$t("settings.invalid_query_ssl_mode");

        if (isValidationOk) {
          this.focusElement("querySslMode");
          isValidationOk = false;
        }
      }

      if (
        this.webHost.trim() &&
        !/^[a-z0-9.-]+$/i.test(this.webHost.trim())
      ) {
        this.error.webHost = this.$t("settings.invalid_web_host");

        if (isValidationOk) {
          this.focusElement("webHost");
          isValidationOk = false;
        }
      }
      return isValidationOk;
    },
    configureModuleValidationFailed(validationErrors) {
      this.loading.configureModule = false;
      let focusAlreadySet = false;

      for (const validationError of validationErrors) {
        const field = validationError.field;

        if (field !== "(root)") {
          // set i18n error message
          if (Object.hasOwn(this.error, field)) {
            this.error[field] = this.$t("settings." + validationError.error);
          }

          if (!focusAlreadySet) {
            this.focusElement(field);
            focusAlreadySet = true;
          }
        }
      }
    },
    async configureModule() {
      const isValidationOk = this.validateConfigureModule();
      if (!isValidationOk) {
        return;
      }

      this.loading.configureModule = true;
      const taskAction = "configure-module";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.configureModuleAborted
      );

      // register to task validation
      this.core.$root.$once(
        `${taskAction}-validation-failed-${eventId}`,
        this.configureModuleValidationFailed
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.configureModuleCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            timezone: this.timezone,
            license_key: this.licenseKey,
            query_ssl_mode: Number(this.querySslMode),
            web_enabled: this.selectValueToBoolean(this.webEnabled),
            web_host: this.webHost.trim().toLowerCase(),
            web_lets_encrypt: this.selectValueToBoolean(this.webLetsEncrypt),
            music_enabled: this.selectValueToBoolean(this.musicEnabled),
            vpn_check_enabled: this.selectValueToBoolean(
              this.vpnCheckEnabled
            ),
          },
          extra: {
            title: this.$t("settings.configure_instance", {
              instance: this.instanceName,
            }),
            description: this.$t("common.processing"),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.configureModule = this.getErrorMessage(err);
        this.loading.configureModule = false;
      }
    },
    configureModuleAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.configureModule = this.$t("error.generic_error");
      this.loading.configureModule = false;
    },
    configureModuleCompleted() {
      this.loading.configureModule = false;

      // reload configuration
      this.getConfiguration();
    },
    booleanToSelectValue(value, defaultValue) {
      if (value === undefined || value === null) {
        return defaultValue ? "1" : "0";
      }
      return value ? "1" : "0";
    },
    selectValueToBoolean(value) {
      return value === "1";
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.bx--form-item {
  margin-bottom: $spacing-05;
}
</style>
