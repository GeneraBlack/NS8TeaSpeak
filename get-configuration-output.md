# get-configuration output Schema

```txt
http://schema.nethserver.org/teaspeak/get-configuration-output.json
```

Get TeaSpeak configuration

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                     |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [get-configuration-output.json](teaspeak/get-configuration-output.json "open original schema") |

## get-configuration output Type

`object` ([get-configuration output](get-configuration-output.md))

# get-configuration output Properties

| Property                                  | Type      | Required | Nullable       | Defined by                                                                                                                                                                               |
| :---------------------------------------- | :-------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [timezone](#timezone)                     | `string`  | Required | cannot be null | [get-configuration output](get-configuration-output-properties-timezone.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/timezone")                   |
| [license\_key](#license_key)              | `string`  | Required | cannot be null | [get-configuration output](get-configuration-output-properties-license_key.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/license_key")             |
| [query\_ssl\_mode](#query_ssl_mode)       | `integer` | Required | cannot be null | [get-configuration output](get-configuration-output-properties-query_ssl_mode.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/query_ssl_mode")       |
| [web\_enabled](#web_enabled)              | `boolean` | Required | cannot be null | [get-configuration output](get-configuration-output-properties-web_enabled.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/web_enabled")             |
| [web\_host](#web_host)                    | `string`  | Required | cannot be null | [get-configuration output](get-configuration-output-properties-web_host.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/web_host")                   |
| [web\_lets\_encrypt](#web_lets_encrypt)   | `boolean` | Required | cannot be null | [get-configuration output](get-configuration-output-properties-web_lets_encrypt.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/web_lets_encrypt")   |
| [music\_enabled](#music_enabled)          | `boolean` | Required | cannot be null | [get-configuration output](get-configuration-output-properties-music_enabled.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/music_enabled")         |
| [vpn\_check\_enabled](#vpn_check_enabled) | `boolean` | Required | cannot be null | [get-configuration output](get-configuration-output-properties-vpn_check_enabled.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/vpn_check_enabled") |

## timezone



`timezone`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-timezone.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/timezone")

### timezone Type

`string`

## license\_key



`license_key`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-license_key.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/license_key")

### license\_key Type

`string`

## query\_ssl\_mode



`query_ssl_mode`

* is required

* Type: `integer`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-query_ssl_mode.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/query_ssl_mode")

### query\_ssl\_mode Type

`integer`

## web\_enabled



`web_enabled`

* is required

* Type: `boolean`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-web_enabled.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/web_enabled")

### web\_enabled Type

`boolean`

## web\_host



`web_host`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-web_host.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/web_host")

### web\_host Type

`string`

## web\_lets\_encrypt



`web_lets_encrypt`

* is required

* Type: `boolean`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-web_lets_encrypt.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/web_lets_encrypt")

### web\_lets\_encrypt Type

`boolean`

## music\_enabled



`music_enabled`

* is required

* Type: `boolean`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-music_enabled.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/music_enabled")

### music\_enabled Type

`boolean`

## vpn\_check\_enabled



`vpn_check_enabled`

* is required

* Type: `boolean`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-vpn_check_enabled.md "http://schema.nethserver.org/teaspeak/get-configuration-output.json#/properties/vpn_check_enabled")

### vpn\_check\_enabled Type

`boolean`
