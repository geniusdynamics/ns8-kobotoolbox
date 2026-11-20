<!--
  Copyright (C) 2022 Nethesis S.r.l.
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
              :label="$t('settings.kobotoolbox_fqdn')"
              placeholder="kobotoolbox.example.org"
              v-model.trim="host"
              class="mg-bottom"
              :invalid-message="$t(error.host)"
              :disabled="loading.getConfiguration || loading.configureModule"
              ref="host"
            >
            </cv-text-input>
            <cv-toggle
              value="letsEncrypt"
              :label="$t('settings.lets_encrypt')"
              v-model="isLetsEncryptEnabled"
              :disabled="loading.getConfiguration || loading.configureModule"
              class="mg-bottom"
            >
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </cv-toggle>
            <cv-toggle
              value="httpToHttps"
              :label="$t('settings.http_to_https')"
              v-model="isHttpToHttpsEnabled"
              :disabled="loading.getConfiguration || loading.configureModule"
              class="mg-bottom"
            >
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </cv-toggle>
              <!-- advanced options -->
            <cv-accordion ref="accordion" class="maxwidth mg-bottom">
              <cv-accordion-item :open="toggleAccordion[0]">
                <template slot="title">{{ $t("settings.advanced") }}</template>
                <template slot="content">
                </template>
              </cv-accordion-item>
            </cv-accordion>

            <NsToggle
              v-model="oidc.enabled"
              :label="$t('settings.oidc_enable')"
              :disabled="loading.getConfiguration || loading.configureModule"
              class="mg-bottom"
            />
            <template v-if="oidc.enabled">
              <NsInlineNotification
                kind="info"
                :title="$t('settings.oidc_enable')"
                :description="$t('settings.oidc_behavior')"
                :showCloseButton="false"
                class="mg-bottom"
              />
              <NsTextInput
                v-model.trim="oidc.name"
                :label="$t('settings.oidc_name')"
                :disabled="loading.getConfiguration || loading.configureModule"
                :invalid-message="error.oidc_name"
                ref="oidc_name"
                class="mg-bottom"
              />
              <NsTextInput
                v-model.trim="oidc.issuer"
                :label="$t('settings.oidc_issuer')"
                :disabled="loading.getConfiguration || loading.configureModule"
                :invalid-message="error.oidc_issuer"
                ref="oidc_issuer"
                class="mg-bottom"
              />
              <NsTextInput
                v-model.trim="oidc.client_id"
                :label="$t('settings.oidc_client_id')"
                :disabled="loading.getConfiguration || loading.configureModule"
                :invalid-message="error.oidc_client_id"
                ref="oidc_client_id"
                class="mg-bottom"
              />
              <NsTextInput
                type="password"
                v-model="oidc.client_secret"
                :label="$t('settings.oidc_client_secret')"
                :disabled="loading.getConfiguration || loading.configureModule"
                :invalid-message="error.oidc_client_secret"
                ref="oidc_client_secret"
                class="mg-bottom"
                :helper-text="oidcSecretConfigured ? $t('settings.oidc_secret_saved') : ''"
                autocomplete="new-password"
              />
              <p v-if="oidcCallbackUrl" class="mg-bottom">
                {{ $t("settings.oidc_callback") }} <code>{{ oidcCallbackUrl }}</code>
              </p>
            </template>
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
      host: "",
      oidc: { enabled: false, issuer: "", client_id: "", client_secret: "", name: "" },
      oidcSecretConfigured: false,
      oidcCallbackPath: "",

      isLetsEncryptEnabled: false,
      isHttpToHttpsEnabled: true,
      loading: {
        getConfiguration: false,
        configureModule: false,
      },
      error: {
        getConfiguration: "",
        configureModule: "",
        oidc_name: "",
        oidc_issuer: "",
        oidc_client_id: "",
        oidc_client_secret: "",
        host: "",
        lets_encrypt: "",
        http2https: "",
      },
    };
  },
  computed: {
    oidcCallbackUrl() {
      if (!this.host) return "";
      return this.oidcCallbackPath ? `https://${this.host}${this.oidcCallbackPath}` : "";
    },

    ...mapState(["instanceName", "core", "appName"]),
  },
  created() {
    this.getConfiguration();
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
        return;
      }
    },
    getConfigurationAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.getConfiguration = this.$t("error.generic_error");
      this.loading.getConfiguration = false;
    },
    getConfigurationCompleted(taskContext, taskResult) {
      const config = taskResult.output;
      this.host = config.host;
      const saved = config.oidc || {};
      this.oidc.enabled = Boolean(saved.enabled);
      this.oidc.issuer = saved.issuer || "";
      this.oidc.client_id = saved.client_id || "";
      this.oidc.client_secret = "";
      this.oidcSecretConfigured = Boolean(saved.secret_configured);
      this.oidcCallbackPath = saved.callback_path || "";
      this.oidc.name = saved.name || "";
      this.isLetsEncryptEnabled = config.lets_encrypt;
      this.isHttpToHttpsEnabled = config.http2https;

      this.loading.getConfiguration = false;
      this.focusElement("host");
    },
    validateConfigureModule() {
      this.clearErrors(this);

      let isValidationOk = true;
      if (!this.host) {
        this.error.host = "common.required";

        if (isValidationOk) {
          this.focusElement("host");
        }
        isValidationOk = false;
      }
      if (this.oidc.enabled && isValidationOk) {
        const fields = ["issuer", "client_id"];
        for (const field of fields) {
          if (!this.oidc[field]) {
            const input = "oidc_" + field;
            this.error[input] = this.$t("common.required");
            this.focusElement(input);
            return false;
          }
        }
      }
      return isValidationOk;
    },
    configureModuleValidationFailed(validationErrors) {
      this.loading.configureModule = false;
      let focusAlreadySet = false;

      for (const validationError of validationErrors) {
        const param = validationError.parameter;
        // set i18n error message
        this.error[param] = this.$t("settings." + validationError.error);

        if (!focusAlreadySet) {
          this.focusElement(param);
          focusAlreadySet = true;
        }
      }
    },
    async configureModule() {
      this.error.test_imap = false;
      this.error.test_smtp = false;
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
            host: this.host,
            oidc: this.oidc.enabled ? { ...this.oidc } : { enabled: false },
            lets_encrypt: this.isLetsEncryptEnabled,
            http2https: this.isHttpToHttpsEnabled,
          },
          extra: {
            title: this.$t("settings.instance_configuration", {
              instance: this.instanceName,
            }),
            description: this.$t("settings.configuring"),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.configureModule = this.getErrorMessage(err);
        this.loading.configureModule = false;
        return;
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
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";
.mg-bottom {
  margin-bottom: $spacing-06;
}

.maxwidth {
  max-width: 38rem;
}
</style>