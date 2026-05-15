<!--
  Copyright (C) 2023 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("status.title") }}</h2>
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getStatus">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-status')"
          :description="error.getStatus"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="error.listBackupRepositories">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.list-backup-repositories')"
          :description="error.listBackupRepositories"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="error.listBackups">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.list-backups')"
          :description="error.listBackups"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getRuntimeInfo">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-runtime-info')"
          :description="error.getRuntimeInfo"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getInitialCredentials">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-initial-credentials')"
          :description="error.getInitialCredentials"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column :md="4" :max="4">
        <NsInfoCard
          light
          :title="status.instance || '-'"
          :description="$t('status.app_instance')"
          :icon="Application32"
          :loading="loading.getStatus"
          class="min-height-card"
        />
      </cv-column>
      <cv-column :md="4" :max="4">
        <NsInfoCard
          light
          :title="installationNodeTitle"
          :titleTooltip="installationNodeTitleTooltip"
          :description="$t('status.installation_node')"
          :icon="Chip32"
          :loading="loading.getStatus"
          class="min-height-card"
        />
      </cv-column>
      <cv-column :md="4" :max="4">
        <NsBackupCard
          :title="core.$t('backup.title')"
          :noBackupMessage="core.$t('backup.no_backup_configured')"
          :goToBackupLabel="core.$t('backup.go_to_backup')"
          :repositoryLabel="core.$t('backup.repository')"
          :statusLabel="core.$t('common.status')"
          :statusSuccessLabel="core.$t('common.success')"
          :statusNotRunLabel="core.$t('backup.backup_has_not_run_yet')"
          :statusErrorLabel="core.$t('error.error')"
          :completedLabel="core.$t('backup.completed')"
          :durationLabel="core.$t('backup.duration')"
          :totalSizeLabel="core.$t('backup.total_size')"
          :totalFileCountLabel="core.$t('backup.total_file_count')"
          :backupDisabledLabel="core.$t('common.disabled')"
          :showMoreLabel="core.$t('common.show_more')"
          :multipleUncertainStatusLabel="
            core.$t('backup.some_backups_failed_or_are_pending')
          "
          :moduleId="instanceName"
          :moduleUiName="instanceLabel"
          :repositories="backupRepositories"
          :backups="backups"
          :loading="loading.listBackupRepositories || loading.listBackups"
          :coreContext="core"
          light
        />
      </cv-column>
      <cv-column :md="4" :max="4">
        <NsSystemLogsCard
          :title="core.$t('system_logs.card_title')"
          :description="
            core.$t('system_logs.card_description', {
              name: instanceLabel || instanceName,
            })
          "
          :buttonLabel="core.$t('system_logs.card_button_label')"
          :router="core.$router"
          context="module"
          :moduleId="instanceName"
          light
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <NsInlineNotification
          kind="info"
          :title="$t('status.initial_credentials_title')"
          :description="$t('status.initial_credentials_hint')"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $t("status.runtime_integration") }}</h4>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <div v-if="loading.getRuntimeInfo">
            <cv-skeleton-text
              :paragraph="true"
              :line-count="6"
            ></cv-skeleton-text>
          </div>
          <div v-else>
            <cv-structured-list>
              <template slot="headings">
                <cv-structured-list-heading>{{
                  $t("status.name")
                }}</cv-structured-list-heading>
                <cv-structured-list-heading>{{
                  $t("status.value")
                }}</cv-structured-list-heading>
              </template>
              <template slot="items">
                <cv-structured-list-item>
                  <cv-structured-list-data>{{
                    $t("status.server_version")
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    runtimeInfo.server_version || "-"
                  }}</cv-structured-list-data>
                </cv-structured-list-item>
                <cv-structured-list-item>
                  <cv-structured-list-data>{{
                    $t("status.credential_capture_status")
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    credentialCaptureStatus
                  }}</cv-structured-list-data>
                </cv-structured-list-item>
                <cv-structured-list-item>
                  <cv-structured-list-data>{{
                    $t("status.captured_at")
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    runtimeInfo.credentials_captured_at || "-"
                  }}</cv-structured-list-data>
                </cv-structured-list-item>
                <cv-structured-list-item>
                  <cv-structured-list-data>{{
                    $t("status.web_client_status")
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    featureStatus(runtimeInfo.web_enabled)
                  }}</cv-structured-list-data>
                </cv-structured-list-item>
                <cv-structured-list-item>
                  <cv-structured-list-data>{{
                    $t("status.web_route_status")
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    teaWebRouteStatus
                  }}</cv-structured-list-data>
                </cv-structured-list-item>
                <cv-structured-list-item>
                  <cv-structured-list-data>{{
                    $t("status.web_route_host")
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    runtimeInfo.web_route_host || "-"
                  }}</cv-structured-list-data>
                </cv-structured-list-item>
                <cv-structured-list-item>
                  <cv-structured-list-data>{{
                    $t("status.web_public_url")
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>
                    <a
                      v-if="runtimeInfo.web_public_url"
                      :href="runtimeInfo.web_public_url"
                      target="_blank"
                      rel="noreferrer"
                    >
                      {{ runtimeInfo.web_public_url }}
                    </a>
                    <span v-else>-</span>
                  </cv-structured-list-data>
                </cv-structured-list-item>
                <cv-structured-list-item>
                  <cv-structured-list-data>{{
                    $t("status.web_certificate_mode")
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    teaWebCertificateMode
                  }}</cv-structured-list-data>
                </cv-structured-list-item>
                <cv-structured-list-item>
                  <cv-structured-list-data>{{
                    $t("status.music_bot_status")
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    featureStatus(runtimeInfo.music_enabled)
                  }}</cv-structured-list-data>
                </cv-structured-list-item>
              </template>
            </cv-structured-list>
            <p class="status-note">{{ initialCredentialsHint }}</p>
            <div
              v-if="runtimeInfo.credentials_available"
              class="credential-actions"
            >
              <cv-button
                v-if="!showInitialCredentials"
                kind="secondary"
                size="small"
                @click="toggleInitialCredentials"
              >
                {{ $t("status.show_initial_credentials") }}
              </cv-button>
              <cv-button
                v-else
                kind="ghost"
                size="small"
                @click="hideInitialCredentials"
              >
                {{ $t("status.hide_initial_credentials") }}
              </cv-button>
            </div>
            <div v-if="showInitialCredentials" class="top-margin-md">
              <cv-skeleton-text
                v-if="loading.getInitialCredentials"
                :paragraph="true"
                :line-count="5"
              ></cv-skeleton-text>
              <cv-structured-list v-else-if="initialCredentials.available">
                <template slot="headings">
                  <cv-structured-list-heading>{{
                    $t("status.name")
                  }}</cv-structured-list-heading>
                  <cv-structured-list-heading>{{
                    $t("status.value")
                  }}</cv-structured-list-heading>
                </template>
                <template slot="items">
                  <cv-structured-list-item>
                    <cv-structured-list-data>{{
                      $t("status.privilege_key")
                    }}</cv-structured-list-data>
                    <cv-structured-list-data class="credential-value">{{
                      initialCredentials.server_admin_privilege_key ||
                      initialCredentials.server_admin_privilege_key_line ||
                      "-"
                    }}</cv-structured-list-data>
                  </cv-structured-list-item>
                  <cv-structured-list-item>
                    <cv-structured-list-data>{{
                      $t("status.query_password")
                    }}</cv-structured-list-data>
                    <cv-structured-list-data class="credential-value">{{
                      initialCredentials.server_query_password ||
                      initialCredentials.server_query_password_line ||
                      "-"
                    }}</cv-structured-list-data>
                  </cv-structured-list-item>
                  <cv-structured-list-item>
                    <cv-structured-list-data>{{
                      $t("status.captured_at")
                    }}</cv-structured-list-data>
                    <cv-structured-list-data>{{
                      initialCredentials.captured_at || "-"
                    }}</cv-structured-list-data>
                  </cv-structured-list-item>
                </template>
              </cv-structured-list>
              <p v-else class="status-note">
                {{ $t("status.initial_credentials_missing_hint") }}
              </p>
            </div>
          </div>
        </cv-tile>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $t("status.public_ports") }}</h4>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <cv-structured-list>
            <template slot="headings">
              <cv-structured-list-heading>{{
                $t("status.port")
              }}</cv-structured-list-heading>
              <cv-structured-list-heading>{{
                $t("status.protocol")
              }}</cv-structured-list-heading>
              <cv-structured-list-heading>{{
                $t("status.purpose")
              }}</cv-structured-list-heading>
            </template>
            <template slot="items">
              <cv-structured-list-item
                v-for="port in visiblePublicPorts"
                :key="`${port.port}-${port.protocol}`"
              >
                <cv-structured-list-data>{{
                  port.port
                }}</cv-structured-list-data>
                <cv-structured-list-data>{{
                  port.protocol
                }}</cv-structured-list-data>
                <cv-structured-list-data>{{
                  $t(port.purpose)
                }}</cv-structured-list-data>
              </cv-structured-list-item>
            </template>
          </cv-structured-list>
        </cv-tile>
      </cv-column>
    </cv-row>
    <!-- services -->
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $tc("status.services", 2) }}</h4>
      </cv-column>
    </cv-row>
    <cv-row v-if="!loading.getStatus">
      <cv-column v-if="!status.services.length">
        <cv-tile light>
          <NsEmptyState :title="$t('status.no_services')"> </NsEmptyState>
        </cv-tile>
      </cv-column>
      <cv-column
        v-else
        v-for="(service, index) in status.services"
        :key="index"
        :md="4"
        :max="4"
      >
        <NsSystemdServiceCard
          light
          class="min-height-card"
          :serviceName="service.name"
          :active="service.active"
          :failed="service.failed"
          :enabled="service.enabled"
          :icon="Cube32"
        />
      </cv-column>
    </cv-row>
    <cv-row v-else>
      <cv-column :md="4" :max="4">
        <cv-tile light>
          <cv-skeleton-text
            :paragraph="true"
            :line-count="4"
          ></cv-skeleton-text>
        </cv-tile>
      </cv-column>
    </cv-row>
    <!-- images -->
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $tc("status.app_images", 2) }}</h4>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <div v-if="!loading.getStatus">
            <NsEmptyState
              v-if="!status.images.length"
              :title="$t('status.no_images')"
            >
            </NsEmptyState>
            <cv-structured-list v-else>
              <template slot="headings">
                <cv-structured-list-heading>{{
                  $t("status.name")
                }}</cv-structured-list-heading>
                <cv-structured-list-heading>{{
                  $t("status.size")
                }}</cv-structured-list-heading>
                <cv-structured-list-heading>{{
                  $t("status.created")
                }}</cv-structured-list-heading>
              </template>
              <template slot="items">
                <cv-structured-list-item
                  v-for="(image, index) in status.images"
                  :key="index"
                >
                  <cv-structured-list-data class="break-word">{{
                    image.name
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    image.size
                  }}</cv-structured-list-data>
                  <cv-structured-list-data class="break-word">{{
                    image.created
                  }}</cv-structured-list-data>
                </cv-structured-list-item>
              </template>
            </cv-structured-list>
          </div>
          <cv-skeleton-text
            v-else
            :paragraph="true"
            :line-count="5"
          ></cv-skeleton-text>
        </cv-tile>
      </cv-column>
    </cv-row>
    <!-- volumes -->
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $tc("status.app_volumes", 2) }}</h4>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <div v-if="!loading.getStatus">
            <NsEmptyState
              v-if="!status.volumes.length"
              :title="$t('status.no_volumes')"
            >
            </NsEmptyState>
            <cv-structured-list v-else>
              <template slot="headings">
                <cv-structured-list-heading>{{
                  $t("status.name")
                }}</cv-structured-list-heading>
                <cv-structured-list-heading>{{
                  $t("status.mount")
                }}</cv-structured-list-heading>
                <cv-structured-list-heading>{{
                  $t("status.created")
                }}</cv-structured-list-heading>
              </template>
              <template slot="items">
                <cv-structured-list-item
                  v-for="(volume, index) in status.volumes"
                  :key="index"
                >
                  <cv-structured-list-data>{{
                    volume.name
                  }}</cv-structured-list-data>
                  <cv-structured-list-data class="break-word">{{
                    volume.mount
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    volume.created
                  }}</cv-structured-list-data>
                </cv-structured-list-item>
              </template>
            </cv-structured-list>
          </div>
          <cv-skeleton-text
            v-else
            :paragraph="true"
            :line-count="5"
          ></cv-skeleton-text>
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
  TaskService,
  IconService,
  UtilService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";

export default {
  name: "Status",
  mixins: [
    TaskService,
    QueryParamService,
    IconService,
    UtilService,
    PageTitleService,
  ],
  pageTitle() {
    return this.$t("status.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "status",
      },
      urlCheckInterval: null,
      isRedirectChecked: false,
      redirectTimeout: 0,
      status: {
        instance: "",
        services: [],
        images: [],
        volumes: [],
      },
      runtimeInfo: {
        server_version: "",
        credentials_available: false,
        credentials_captured_at: "",
        credentials_source: "",
        web_route_host: "",
        web_route_configured: false,
        web_route_lets_encrypt: false,
        web_public_url: "",
      },
      initialCredentials: {
        available: false,
        server_admin_privilege_key: "",
        server_query_password: "",
        captured_at: "",
        source: "",
        server_admin_privilege_key_line: "",
        server_query_password_line: "",
      },
      showInitialCredentials: false,
      publicPorts: [
        {
          port: "9987",
          protocol: "udp",
          purpose: "status.voice_port",
        },
        {
          port: "9987",
          protocol: "tcp",
          purpose: "status.compatibility_port",
        },
        {
          port: "10101",
          protocol: "tcp",
          purpose: "status.query_port",
        },
        {
          port: "30303",
          protocol: "tcp",
          purpose: "status.file_port",
        },
      ],
      backupRepositories: [],
      backups: [],
      loading: {
        getStatus: false,
        getRuntimeInfo: false,
        getInitialCredentials: false,
        listBackupRepositories: false,
        listBackups: false,
      },
      error: {
        getStatus: "",
        getRuntimeInfo: "",
        getInitialCredentials: "",
        listBackupRepositories: "",
        listBackups: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "instanceLabel", "core", "appName"]),
    installationNodeTitle() {
      if (this.status && this.status.node) {
        if (this.status.node_ui_name) {
          return this.status.node_ui_name;
        } else {
          return this.$t("status.node") + " " + this.status.node;
        }
      } else {
        return "-";
      }
    },
    installationNodeTitleTooltip() {
      if (this.status && this.status.node_ui_name) {
        return this.$t("status.node") + " " + this.status.node;
      } else {
        return "";
      }
    },
    credentialCaptureStatus() {
      if (this.runtimeInfo.credentials_available) {
        return this.$t("status.initial_credentials_available");
      }
      return this.$t("status.initial_credentials_missing");
    },
    initialCredentialsHint() {
      if (this.runtimeInfo.credentials_available) {
        return this.$t("status.initial_credentials_available_hint");
      }
      return this.$t("status.initial_credentials_missing_hint");
    },
    teaWebRouteStatus() {
      if (!this.runtimeInfo.web_enabled) {
        return this.$t("settings.option_disabled");
      }
      return this.$t(
        this.runtimeInfo.web_route_configured
          ? "status.web_route_configured"
          : "status.web_route_missing"
      );
    },
    teaWebCertificateMode() {
      if (!this.runtimeInfo.web_route_host) {
        return "-";
      }
      return this.$t(
        this.runtimeInfo.web_route_lets_encrypt
          ? "status.lets_encrypt_requested"
          : "status.traefik_default_certificate"
      );
    },
    visiblePublicPorts() {
      return this.publicPorts.filter((port) => {
        if (!port.requiresWeb) {
          return true;
        }
        return this.runtimeInfo.web_enabled;
      });
    },
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
  mounted() {
    this.redirectTimeout = setTimeout(
      () => (this.isRedirectChecked = true),
      200
    );
  },
  beforeUnmount() {
    clearTimeout(this.redirectTimeout);
  },
  created() {
    this.getStatus();
    this.getRuntimeInfo();
    this.listBackupRepositories();
  },
  methods: {
    emptyInitialCredentials() {
      return {
        available: false,
        server_admin_privilege_key: "",
        server_query_password: "",
        captured_at: "",
        source: "",
        server_admin_privilege_key_line: "",
        server_query_password_line: "",
      };
    },
    async getStatus() {
      this.loading.getStatus = true;
      this.error.getStatus = "";
      const taskAction = "get-status";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.getStatusAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.getStatusCompleted
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
        this.error.getStatus = this.getErrorMessage(err);
        this.loading.getStatus = false;
      }
    },
    getStatusAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.getStatus = this.$t("error.generic_error");
      this.loading.getStatus = false;
    },
    getStatusCompleted(taskContext, taskResult) {
      this.status = taskResult.output;
      this.loading.getStatus = false;
    },
    async getRuntimeInfo() {
      this.loading.getRuntimeInfo = true;
      this.error.getRuntimeInfo = "";
      const taskAction = "get-runtime-info";
      const eventId = this.getUuid();

      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.getRuntimeInfoAborted
      );

      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.getRuntimeInfoCompleted
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
        this.error.getRuntimeInfo = this.getErrorMessage(err);
        this.loading.getRuntimeInfo = false;
      }
    },
    getRuntimeInfoAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.getRuntimeInfo = this.$t("error.generic_error");
      this.loading.getRuntimeInfo = false;
    },
    getRuntimeInfoCompleted(taskContext, taskResult) {
      this.runtimeInfo = taskResult.output;
      if (!this.runtimeInfo.credentials_available) {
        this.initialCredentials = this.emptyInitialCredentials();
        this.showInitialCredentials = false;
      }
      this.loading.getRuntimeInfo = false;
    },
    async getInitialCredentials() {
      this.loading.getInitialCredentials = true;
      this.error.getInitialCredentials = "";
      const taskAction = "get-initial-credentials";
      const eventId = this.getUuid();

      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.getInitialCredentialsAborted
      );

      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.getInitialCredentialsCompleted
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
        this.error.getInitialCredentials = this.getErrorMessage(err);
        this.loading.getInitialCredentials = false;
      }
    },
    getInitialCredentialsAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.getInitialCredentials = this.$t("error.generic_error");
      this.loading.getInitialCredentials = false;
    },
    getInitialCredentialsCompleted(taskContext, taskResult) {
      this.initialCredentials = taskResult.output;
      this.loading.getInitialCredentials = false;
    },
    toggleInitialCredentials() {
      if (this.showInitialCredentials) {
        this.hideInitialCredentials();
        return;
      }

      this.showInitialCredentials = true;
      if (!this.loading.getInitialCredentials) {
        this.getInitialCredentials();
      }
    },
    hideInitialCredentials() {
      this.showInitialCredentials = false;
    },
    featureStatus(enabled) {
      return this.$t(
        enabled ? "settings.option_enabled" : "settings.option_disabled"
      );
    },
    async listBackupRepositories() {
      this.loading.listBackupRepositories = true;
      this.error.listBackupRepositories = "";
      const taskAction = "list-backup-repositories";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.listBackupRepositoriesAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.listBackupRepositoriesCompleted
      );

      const res = await to(
        this.createClusterTaskForApp({
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
        this.error.listBackupRepositories = this.getErrorMessage(err);
        this.loading.listBackupRepositories = false;
      }
    },
    listBackupRepositoriesAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.listBackupRepositories = this.$t("error.generic_error");
      this.loading.listBackupRepositories = false;
    },
    listBackupRepositoriesCompleted(taskContext, taskResult) {
      let backupRepositories = taskResult.output.repositories.sort(
        this.sortByProperty("name")
      );
      this.backupRepositories = backupRepositories;
      this.loading.listBackupRepositories = false;
      this.listBackups();
    },
    async listBackups() {
      this.loading.listBackups = true;
      this.error.listBackups = "";
      const taskAction = "list-backups";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.listBackupsAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.listBackupsCompleted
      );

      const res = await to(
        this.createClusterTaskForApp({
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
        this.error.listBackups = this.getErrorMessage(err);
        this.loading.listBackups = false;
      }
    },
    listBackupsAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.listBackups = this.$t("error.generic_error");
      this.loading.listBackups = false;
    },
    listBackupsCompleted(taskContext, taskResult) {
      let backups = taskResult.output.backups;
      backups.sort(this.sortByProperty("name"));

      // get repository name
      for (const backup of backups) {
        const repo = this.backupRepositories.find(
          (r) => r.id == backup.repository
        );

        if (repo) {
          backup.repoName = repo.name;
        }
      }
      this.backups = backups;
      this.loading.listBackups = false;
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.break-word {
  word-wrap: break-word;
  max-width: 30vw;
}

.status-note {
  margin-top: 1rem;
  margin-bottom: 0;
}

.credential-actions {
  margin-top: 1rem;
}

.top-margin-md {
  margin-top: 1rem;
}

.credential-value {
  word-break: break-all;
}
</style>
