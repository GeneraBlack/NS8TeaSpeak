# configure-module input Schema

```txt
http://schema.nethserver.org/teaspeak/configure-module-input.json
```

Configure TeaSpeak

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                 |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :----------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [configure-module-input.json](teaspeak/configure-module-input.json "open original schema") |

## configure-module input Type

`object` ([configure-module input](configure-module-input.md))

# configure-module input Properties

| Property                                  | Type      | Required | Nullable       | Defined by                                                                                                                                                                         |
| :---------------------------------------- | :-------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [timezone](#timezone)                     | `string`  | Optional | cannot be null | [configure-module input](configure-module-input-properties-timezone.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/timezone")                   |
| [license\_key](#license_key)              | `string`  | Optional | cannot be null | [configure-module input](configure-module-input-properties-license_key.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/license_key")             |
| [query\_ssl\_mode](#query_ssl_mode)       | `integer` | Optional | cannot be null | [configure-module input](configure-module-input-properties-query_ssl_mode.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/query_ssl_mode")       |
| [web\_enabled](#web_enabled)              | `boolean` | Optional | cannot be null | [configure-module input](configure-module-input-properties-web_enabled.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/web_enabled")             |
| [web\_host](#web_host)                    | `string`  | Optional | cannot be null | [configure-module input](configure-module-input-properties-web_host.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/web_host")                   |
| [web\_lets\_encrypt](#web_lets_encrypt)   | `boolean` | Optional | cannot be null | [configure-module input](configure-module-input-properties-web_lets_encrypt.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/web_lets_encrypt")   |
| [music\_enabled](#music_enabled)          | `boolean` | Optional | cannot be null | [configure-module input](configure-module-input-properties-music_enabled.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/music_enabled")         |
| [vpn\_check\_enabled](#vpn_check_enabled) | `boolean` | Optional | cannot be null | [configure-module input](configure-module-input-properties-vpn_check_enabled.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/vpn_check_enabled") |

## timezone



`timezone`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-timezone.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/timezone")

### timezone Type

`string`

### timezone Constraints

**minimum length**: the minimum number of characters for this string is: `1`

### timezone Default Value

The default value is:

```json
"UTC"
```

## license\_key



`license_key`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-license_key.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/license_key")

### license\_key Type

`string`

### license\_key Default Value

The default value is:

```json
""
```

## query\_ssl\_mode



`query_ssl_mode`

* is optional

* Type: `integer`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-query_ssl_mode.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/query_ssl_mode")

### query\_ssl\_mode Type

`integer`

### query\_ssl\_mode Constraints

**maximum**: the value of this number must smaller than or equal to: `2`

**minimum**: the value of this number must greater than or equal to: `0`

### query\_ssl\_mode Default Value

The default value is:

```json
2
```

## web\_enabled



`web_enabled`

* is optional

* Type: `boolean`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-web_enabled.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/web_enabled")

### web\_enabled Type

`boolean`

### web\_enabled Default Value

The default value is:

```json
true
```

## web\_host



`web_host`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-web_host.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/web_host")

### web\_host Type

`string`

### web\_host Default Value

The default value is:

```json
""
```

## web\_lets\_encrypt



`web_lets_encrypt`

* is optional

* Type: `boolean`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-web_lets_encrypt.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/web_lets_encrypt")

### web\_lets\_encrypt Type

`boolean`

### web\_lets\_encrypt Default Value

The default value is:

```json
false
```

## music\_enabled



`music_enabled`

* is optional

* Type: `boolean`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-music_enabled.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/music_enabled")

### music\_enabled Type

`boolean`

### music\_enabled Default Value

The default value is:

```json
false
```

## vpn\_check\_enabled



`vpn_check_enabled`

* is optional

* Type: `boolean`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-vpn_check_enabled.md "http://schema.nethserver.org/teaspeak/configure-module-input.json#/properties/vpn_check_enabled")

### vpn\_check\_enabled Type

`boolean`

### vpn\_check\_enabled Default Value

The default value is:

```json
false
```
