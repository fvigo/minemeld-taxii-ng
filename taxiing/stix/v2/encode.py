import uuid
import logging

from datetime import datetime

LOG = logging.getLogger(__name__)


TLP_MARKING_DEFINITIONS = {
    'white': 'marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9',
    'green': 'marking-definition--34098fce-860f-48ae-8e50-ebd3cc5e41da',
    'amber': 'marking-definition--f88d31f6-486f-44da-b317-01333bde0b82',
    'red': 'marking-definition--5e57c739-391a-4eb3-b6be-7d15ca92d5ed'
}


TYPE_CONVERSION = {
    'IPv4': 'ipv4-addr:value',
    'IPv6': 'ipv6-addr:value',
    'domain': 'domain-name:value',
    'URL': 'url:value',
    'sha256': "file:hashes.'SHA-256'",
    'sha1': "file:hashes.'SHA-1'",
    'sha512': "file:hashes.'SHA-512'",
    'md5': "file:hashes.MD5",
    'ssdeep': "file:hashes.ssdeep"
}


NAME_ATTRIBUTES = [
    'stix2_name',
    'stix_title',
    'stix_package_title'
]


DESCRIPTION_ATTRIBUTES = [
    'stxi2_description',
    'stix_description',
    'stix_package_description'
]


def _indicator_to_pattern(indicator, type_):
    if type_ == 'stix2-pattern':
        return indicator

    stix2_pattern = TYPE_CONVERSION.get(type_, None)
    if stix2_pattern is None:
        raise RuntimeError('Unhandled type {!r}'.format(type_))

    return "[{} = '{}']".format(stix2_pattern, indicator)


def _get_name(indicator, type_, value):
    result = value.get('stix2_name', None)
    if result is not None:
        return result

    return '{} indicator: {}'.format(type_, indicator)


def _get_name(indicator, type_, value):
    result = value.get('stix2_name', None)
    if result is not None:
        return result

    return '{} indicator: {}'.format(type_, indicator)


def _get_description(indicator, type_, value):
    result = value.get('stix2_description', None)
    if result is not None:
        return result

    return '{} indicator {}, received from {}'.format(
        type_,
        indicator,
        ', '.join(value.get('sources', []))
    )


def _get_id(indicator, type_, value):
    result = value.get('stix2_id', None)
    if result is not None:
        return result

    return 'indicator--'+str(uuid.uuid3(uuid.NAMESPACE_URL, 'minemeld/{}/{}/{}'.format(
        value.get('type', 'unknown'),
        indicator,
        value.get('last_seen', 0)
    )))


def _additional_properties(indicator, type_, value):
    result = {}

    labels = value.get('stix2_labels', None)
    if labels is not None:
        result['labels'] = labels

    information_source = value.get('stix_information_source', None)
    if information_source is not None:
        result['_created_by_ref'] = 'organization:'+information_source

    created_by_ref = value.get('stix2_created_by', None)
    if created_by_ref is not None:
        result['_created_by_ref'] = created_by_ref

    return result


def _to_stix2_timestamp(dt):
    # YYYY-MM-DDTHH:mm:ss.sssZ
    result = dt.strftime('%Y-%m-%dT%H:%M:%S')
    result = result+('.{:03d}Z'.format(int(dt.microsecond/1000)))
    return result


def encode(indicator, value, feedname=''):
    type_ = value.get('type', None)
    if type_ is None:
        raise RuntimeError('No type in indicator')

    result = {
        'type': 'indicator',
        'name': _get_name(indicator, type_, value),
        'description': _get_description(indicator, type_, value),
        'id': _get_id(indicator, type_, value),
        'pattern': _indicator_to_pattern(indicator, type_)
    }
    
    last_seen = value.get('last_seen', None)
    if last_seen is not None:
        result['modified'] = _to_stix2_timestamp(datetime.utcfromtimestamp(last_seen/1000))

    first_seen = value.get('first_seen', None)
    if first_seen is not None:
        first_seen = _to_stix2_timestamp(datetime.utcfromtimestamp(last_seen/1000))
        result['valid_from'] = first_seen
        result['created'] = first_seen
    else:
        result['valid_from'] = _to_stix2_timestamp(datetime.utcnow())

    share_level = value.get('share_level', None)
    if share_level is not None and share_level in TLP_MARKING_DEFINITIONS:
        result['object_marking_refs'] = [TLP_MARKING_DEFINITIONS[share_level]]

    result.update(_additional_properties(indicator, type_, value))

    return result
